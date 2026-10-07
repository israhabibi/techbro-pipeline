# Security

Do not post tokens, cookies, personal timeline data, or private host information
in issues. For a suspected vulnerability, use GitHub's private vulnerability
reporting feature if enabled, or contact the repository owner privately through
an existing channel. Do not publish exploit details before a fix is available.

Keep `creds.json` and `.env` local with restricted filesystem permissions. If a
cookie or key is exposed, revoke or rotate it and remove the disclosure from the
relevant history. `.gitignore` does not remove older commits containing data.

The dashboard defaults to loopback access. Authenticate it at the reverse proxy
before making a personal archive reachable externally. API keys remain server-side;
chat requests have bounded input sizes and constrained message roles. Video assets
are selected through administrator configuration, not arbitrary client paths.

The container runs without root or Linux capabilities and excludes secrets,
datasets, and runtime data from its build context. Preserve these exclusions.
Run `make audit` and `npm audit` regularly. Audit results cover known published
Python/Node vulnerabilities, not every operating-system package or possible defect.
