from app.services.vector_store import PseudoVectorStore


def test_vector_store_returns_relevant_article():
    store = PseudoVectorStore([
        {"article_id":"A","title":"Failed debit reversal","category":"failed_debited","symptoms":["failed","amount deducted"],"resolution":"Check reversal ledger.","routing_keywords":["reversal"]},
        {"article_id":"B","title":"Fee dispute","category":"fee_or_amount_dispute","symptoms":["fee charged"],"resolution":"Check tariff.","routing_keywords":["finance"]},
    ])
    hits = store.search("The transfer failed but my amount was deducted", top_k=1)
    assert hits[0].article_id == "A"
    assert hits[0].score > 0
