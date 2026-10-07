# Optional ingress

The default Compose service binds to localhost. Use a single existing reverse
proxy with authentication before exposing personal archive data. A standalone
Caddy example is in `../native/Caddyfile.example`; replace the example domain and
password hash. Do not commit personal host configurations or authentication hashes.

An existing Traefik container can keep using its local ignored `traefik.yml` and
`dynamic.yml`. Keep it on the dashboard's Compose network if its backend is
`http://digest:8000`. Do not start another proxy on the same ports.
