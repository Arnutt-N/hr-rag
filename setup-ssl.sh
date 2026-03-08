#!/bin/bash
# SSL Setup Script for HR-RAG
# Usage: ./setup-ssl.sh your-domain.com

set -e

DOMAIN=${1:-""}

if [ -z "$DOMAIN" ]; then
    echo "❌ กรุณาระบุ domain"
    echo "Usage: ./setup-ssl.sh your-domain.com"
    exit 1
fi

echo "🔧 Setting up SSL for: $DOMAIN"

# Create directories
mkdir -p certbot/conf certbot/www

# Replace domain in nginx.conf
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf

echo "🚀 Starting nginx (temporary without SSL)..."
docker-compose up -d nginx

echo "⏳ Waiting for nginx to start..."
sleep 5

echo "🔒 Obtaining SSL certificate from Let's Encrypt..."
docker run -it --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

echo "🔄 Reloading nginx with SSL..."
docker-compose exec nginx nginx -s reload

echo "✅ SSL setup complete!"
echo ""
echo "🌐 Your site is now available at:"
echo "   https://$DOMAIN"
echo ""
echo "📅 SSL will auto-renew. To test renewal:"
echo "   docker-compose exec certbot certbot renew --dry-run"
