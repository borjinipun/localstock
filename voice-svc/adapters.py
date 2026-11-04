"""Provider adapters (spec docs 08 §5). MVP: MockAdapter; Exotel/Meta stubs raise
NotImplementedError until Phase-0 contracts & keys exist (docs 10 OQ-07)."""

import dialog as dia


class Adapter:
    def flows(self, *args, **kwargs):
        raise NotImplementedError


class MockAdapter(Adapter):
    """Deterministic script engine. Docstrings = simulated shop behaviour map."""

    def flows(self, behavior, channels, item_intent, target_id, attempt_id):
        return dia.build_flows(behavior, channels, item_intent, target_id, attempt_id)


class ExotelAdapter(Adapter):
    """Outbound voice via Exotel. Not configured in MVP — see docs 08 §5 spike."""
    def flows(self, *args, **kwargs):
        raise NotImplementedError("Exotel adapter needs Phase-0 contract (docs 10 OQ-07)")


class MetaWhatsAppAdapter(Adapter):
    """Utility-template WhatsApp interactions per docs 03 §5. Not wired at MVP."""
    def flows(self, *args, **kwargs):
        raise NotImplementedError("Meta WhatsApp adapter needs Meta template approval")


def get_adapter(kind_env: str):
    return {"mock": MockAdapter(), "exotel": ExotelAdapter(),
            "meta_cloud": MetaWhatsAppAdapter()}.get(kind_env) or MockAdapter()
