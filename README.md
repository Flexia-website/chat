# Flexia Merchant Chat Application

A real-time chat application with user management, image uploads, and admin panel.

## Features

- Real-time messaging with Socket.IO
- User registration with 7-day expiration
- Image upload support
- Admin panel for managing conversations
- Responsive design
- SQLite database for data persistence

## Deployment on Render

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/flexia-merchant-chat)

### Manual Deployment

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your repository
4. Add environment variables:
   - `SECRET_KEY`: Generate a random string
   - `ADMIN_PASSWORD`: Your admin password
   - `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`: Keypair for background push notifications to the admin app. Dev defaults are baked in so it works out of the box, but generate your own for production:
     ```bash
     pip install pywebpush --break-system-packages
     python3 -c "
     from py_vapid import Vapid
     from cryptography.hazmat.primitives import serialization
     import base64
     v = Vapid(); v.generate_keys()
     b64 = lambda d: base64.urlsafe_b64encode(d).rstrip(b'=').decode()
     print('VAPID_PRIVATE_KEY=', b64(v.private_key.private_numbers().private_value.to_bytes(32, 'big')))
     print('VAPID_PUBLIC_KEY=', b64(v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)))
     "
     ```
   - `VAPID_CLAIMS_EMAIL`: A `mailto:` address for push service contact (optional, defaults to a placeholder)
5. Add persistent disk for uploads
6. Deploy!

## Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/flexia-merchant-chat.git
cd flexia-merchant-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python server.py

# Access at http://localhost:5000
# Admin at http://localhost:5000/123456.html (default password)