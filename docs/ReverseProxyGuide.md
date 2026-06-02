# Reverse Proxy Guide

## Current Warning

The MVP currently serves HTTP directly:

- Frontend: `http://10.0.44.2:3000`
- Backend API: `http://10.0.44.2:8000`

This is acceptable only for controlled internal demos. For wider use, put Nginx or another reverse proxy in front and use HTTPS.

## Recommended Layout

```text
Browser
  -> https://academy.example.com/
      -> Nginx reverse proxy
          /      -> frontend http://127.0.0.1:3000
          /api/  -> backend  http://127.0.0.1:8000
          /docs  -> backend  http://127.0.0.1:8000
```

Keep Docker Compose direct ports during MVP testing unless you intentionally firewall them.

## CORS Notes

When using a domain, add the HTTPS origin to `deployments/env/backend.env`:

```env
CORS_ORIGINS=https://academy.example.com,http://10.0.44.2:3000
```

Restart the backend after changing CORS.

## Example Nginx Config

See:

```text
deployments/nginx/isp-academy.conf.example
```

Install it as needed:

```bash
sudo cp deployments/nginx/isp-academy.conf.example /etc/nginx/sites-available/isp-academy
sudo ln -s /etc/nginx/sites-available/isp-academy /etc/nginx/sites-enabled/isp-academy
sudo nginx -t
sudo systemctl reload nginx
```

## Self-Signed Certificate For LAN

For a LAN-only demo without a public domain, use a self-signed certificate and distribute/trust it only on demo machines.

Example:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/isp-academy.key \
  -out /etc/ssl/certs/isp-academy.crt
```

Browsers will warn unless the certificate is trusted by the client.

## Let's Encrypt For Real Domain

For a real domain pointing to this server:

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d academy.example.com
```

Confirm firewall rules allow HTTP/HTTPS during issuance.

## Future WebSocket Note

Router console and web terminal are not implemented in Phase 10. If added later, proxy WebSocket paths with:

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

Do not expose arbitrary SSH or router command access through the proxy.
