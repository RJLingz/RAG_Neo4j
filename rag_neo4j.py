# -*- coding: utf-8 -*-
"""RAG_NEO4J.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1pUNotOFsOGwzDw4sZHN5MAuYUh_6Blwm
"""

from dotenv import load_dotenv
import os
from langchain_community.graphs import Neo4jGraph
from langchain.vectorstores.neo4j_vector import Neo4jVector
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentType
from langchain.agents import AgentExecutor, create_structured_chat_agent


# Load environment variables from .env file
load_dotenv()

# Neo4j connection details
neo4j_url = os.getenv("NEO4J_URL")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_database = os.getenv("NEO4J_DATABASE")

# OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

class MovieNeo4jLoader:
    def __init__(self, url, username, password, database):
        self.graph = Neo4jGraph(url=url, username=username, password=password, database=database)

    def load_movies_data(self):
        movies_query = """
        LOAD CSV WITH HEADERS FROM 'https://raw.githubusercontent.com/tomasonjo/blog-datasets/main/movies/movies_small.csv'
        AS row
        MERGE (m:Movie {id:row.movieId})
        SET m.released = date(row.released),
            m.title = row.title,
            m.imdbRating = toFloat(row.imdbRating)
        FOREACH (director in split(row.director, '|') |
            MERGE (p:Person {name:trim(director)})
            MERGE (p)-[:DIRECTED]->(m))
        FOREACH (actor in split(row.actors, '|') |
            MERGE (p:Person {name:trim(actor)})
            MERGE (p)-[:ACTED_IN]->(m))
        FOREACH (genre in split(row.genres, '|') |
            MERGE (g:Genre {name:trim(genre)})
            MERGE (m)-[:IN_GENRE]->(g))
        """
        self.graph.query(movies_query)

class VectorSimilarity:
    """
    Class to set up vector similarity using Neo4j and OpenAI embeddings.
    """
    def __init__(self, url, username, password, embeddings_model):
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.vector_index = Neo4jVector.from_existing_graph(
            OpenAIEmbeddings(model=embeddings_model),
            url=url,
            username=username,
            password=password,
            index_name='movies',
            node_label="Movie",
            text_node_properties=['title', 'released', 'imdbRating'],
            embedding_node_property='embedding',
        )

class QAHandlers:
    """
    Class to handle different QA chains using Neo4j for retrieval and Cypher queries.
    """
    def __init__(self, url, username, password):
        self.graph = Neo4jGraph(url=url, username=username, password=password)

    def setup_qa_chains(self):
        self.vector_qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
            chain_type="stuff",
            retriever=self.vector_index.as_retriever()
        )

        self.cypher_chain = GraphCypherQAChain.from_llm(
            cypher_llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
            qa_llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
            graph=self.graph,
            verbose=True
        )

class AgentInitializer:
    """
    Class to initialize agents with specific tools and models.
    """
    def __init__(self, tools):
        self.agent = initialize_agent(
            tools,
            ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True
        )

if __name__ == "__main__":

    question = sys.argv[1]  # Retrieve the first command-line argument
    # Initialize components
    movie_loader = MovieNeo4jLoader(neo4j_url, neo4j_username, neo4j_password, neo4j_database)
    movie_loader.load_movies_data()

    vector_similarity = VectorSimilarity(neo4j_url, neo4j_username, neo4j_password, "text-embedding-3-small")

    qa_handlers = QAHandlers(neo4j_url, neo4j_username, neo4j_password)
    qa_handlers.setup_qa_chains()

    ###templates

    # Using with chat history


    system = '''Respond to the human as helpfully and accurately as possible. You have access to the following tools:

    {tools}

    Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

    Valid "action" values: "Final Answer" or {tool_names}

    Provide only ONE action per $JSON_BLOB, as shown:

    ```
    {{
      "action": $TOOL_NAME,
      "action_input": $INPUT
    }}
    ```

    Follow this format:

    Question: input question to answer
    Thought: consider previous and subsequent steps
    Action:
    ```
    $JSON_BLOB
    ```
    Observation: action result
    ... (repeat Thought/Action/Observation N times)
    Thought: I know what to respond
    Action:
    ```
    {{
      "action": "Final Answer",
      "action_input": "Final response to human"
    }}

    Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation
    Introduce yourself first and say Hi, I am your local movie boffin and I am here to answer all your questions about movies. Please proceed to ask me a question
    '''



    human = '''{input}

    {agent_scratchpad}

    (reminder to respond in a JSON blob no matter what)'''

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human),
        ]
    )

    # Define tools for the agent
    tools = [
        Tool(
            name="Tasks",
            func=qa_handlers.vector_qa.run,
            description="""Useful when you need to answer questions about movies
            and their title as well as their rating and the year they were released.
            Use full question as input.
            """,
        ),
        Tool(
            name="Graph",
            func=qa_handlers.cypher_chain.run,
            description="""Useful when you need to answer questions about movies and their genres,
            their directors or any complex calculations such as counting movies people appear in.
            Use full question as input.
            """,
        )
    ]

    # Initialize agent

    agent = create_structured_chat_agent(ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"), tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    #####execute the code
    agent_executor.invoke({"input": question,
            })