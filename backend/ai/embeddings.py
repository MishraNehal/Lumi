from langchain_huggingface import HuggingFaceEmbeddings



def get_embedding_model():
    """
    Returns embedding model used across the project
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


