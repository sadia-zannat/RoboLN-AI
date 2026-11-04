# Proxy reset investigation

The original reported Windows errors named telemetry/history, telemetry/twin and controls. Their corresponding backend traceback/process exit was not supplied; the exact laptop root cause remains unconfirmed.

Confirmed source defects were overlapping fixed-interval polling, surviving pending requests after navigation and missing browser time bounds. The opaque Next rewrite was replaced by an explicit Node HTTP/HTTPS proxy: per-request connections (`agent:false`, `Connection: close`), no mutation retry, 6 MB request/20 MB response limits, 85-second upstream timeout, visible 502 reset/504 timeout errors and correlation IDs. Real backend authorization/database errors are forwarded, not replaced by empty success data. SQLite waits up to 15 seconds and operational errors return a structured 503.

The room reads one coherent snapshot with serialized polling, cancellation on route/mode leave and hidden-page pause. Snapshot failure labels retained data historical/unavailable and disables live eligibility. Six local TCP proxy tests cover status/cookie/body forwarding, fresh sockets, forced reset, timeout and size/path rejection. Browser regressions repeatedly read all three original routes across idle gaps, navigation and refresh. Current executed results are in the release report.

If a laptop/host reset recurs, retain both frontend correlation ID/time/code and matching backend traceback/process status. Check direct backend readiness, runtime backend URL, database permissions and migrations. Passing local regression tests do not establish the cause of a missing external failure trace.
