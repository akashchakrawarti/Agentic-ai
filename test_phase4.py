"""
test_phase4.py
---------------
Builds the FAISS index from the knowledge base, then runs a few sample
queries through retrieval + grounded LLM explanation - so you can see
RAG working end-to-end before it's wired into the agent/UI.

Run with:  python test_phase4.py

Note: the first run will download the embedding model (~90MB) - this is
a one-time download, cached locally afterward.
"""

from rag import build_index, retrieve, generate_grounded_explanation


TEST_QUERIES = [
    "Why would an IT company with AI upskilling needs be a good fit for Industry-Curated Learning Pods?",
    "What kind of company is a good fit for the Startup Acceleration Program?",
    "Who is the typical decision-maker for Corporate Capability Labs?",
]


def main():
    print("Building knowledge base index (loading embedding model, this may take a moment)...")
    index, documents = build_index()
    print(f"Index built successfully with {len(documents)} knowledge documents.\n")

    for query in TEST_QUERIES:
        print("=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        retrieved_chunks = retrieve(query, index, documents, top_k=2)

        print("\nRETRIEVED CHUNKS:")
        for chunk in retrieved_chunks:
            print(f"  - {chunk['source']} (similarity: {chunk['similarity']:.3f})")

        print("\nGROUNDED EXPLANATION:")
        explanation = generate_grounded_explanation(query, retrieved_chunks)
        print(explanation)
        print()


if __name__ == "__main__":
    main()
