"""voice-svc — orchestrator for the verification engine (docs 03 §4/5/6).

Owns the TelephonyAdapter/WhatsApp/SMS provider integrations. MVP ships a
deterministic MockAdapter driven by scripted shop behaviours so the full
query→check→results flow runs locally end-to-end (docs 09 Phase 0 spike).

Real providers (Exotel/Meta Cloud/relayers) plug in behind the same adapters
with env flags — see Provider guide in the root README.
"""
