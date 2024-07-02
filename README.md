# Movie Knowledge Base Chatbot
Welcome to the Movie Knowledge Base Chatbot project! This chatbot utilizes Neo4j for storing movie data, LangChain for processing natural language queries, and OpenAI's GPT-3.5 for generating responses. It can answer questions related to movies, directors, actors, genres, and more.

## Setup and Installation
### Prerequisites
Python 3.x installed on your system
Access to Neo4j database (either locally or remote)
OpenAI API key
### Installation Steps

1. Clone the repository:

```
    git clone https://github.com/your/repository.git
    cd repository-name
```

3. Install dependencies:
```
   pip install --upgrade --quiet session-info langchain pipreqs openai  tiktoken  python-dotenv transformers    langchain- 
   community langchain-openai neo4j
```

5. Initialize Neo4j database:
   We use the Neo4j website database and initialise a blank database. You will download a file that will habe all your variables that you need to use this example.

6. Set up environment variables:
```
   NEO4J_URL=your_neo4j_url
   NEO4J_USERNAME=your_neo4j_username
   NEO4J_PASSWORD=your_neo4j_password
   NEO4J_DATABASE=your_neo4j_database
   OPENAI_API_KEY=your_openai_api_key

```

8. Run the project
```
   python main.py "what is the actor in Casino?"
```

## Project Architecture 


The project is structured as follows:

main.py: Entry point of the application. Loads movie data into Neo4j, sets up vector similarity, QA handlers, and initializes the chatbot agent.

MovieNeo4jLoader: Class to load movie data from CSV into Neo4j database.

VectorSimilarity: Class to set up vector similarity using OpenAI embeddings and Neo4j.

QAHandlers: Class to set up QA chains using LangChain for answering movie-related queries.

AgentInitializer: Class to initialize the chatbot agent using LangChain and OpenAI.

README.md: This file, containing instructions on how to set up, run, and use the project.

## Interacting with the Chatnot 


## Notes 

Ensure your environment variables (NEO4J_URL, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE, OPENAI_API_KEY) are correctly set before running the application.
Modify the chatbot's behavior or add additional functionalities by extending the tools and handlers defined in main.py.


   
This repository shows how to run a RAG application utilising neo4j and Lanchain agents


