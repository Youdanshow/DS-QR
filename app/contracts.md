# QR Code Generator - API Contracts & Integration Plan

## User Limits System
- **Non-authenticated users**: 3 QR codes maximum (tracked by IP/session)
- **Authenticated users**: 5 QR codes maximum 
- **Premium subscribers**: Unlimited QR code generation

## Authentication System
- JWT-based authentication
- User registration/login
- Password hashing with bcrypt
- Session management

## API Contracts

### Authentication Endpoints
```
POST /api/auth/register
Body: { email, password, name }
Response: { user, token, limits: { used: 0, max: 5, isPremium: false } }

POST /api/auth/login  
Body: { email, password }
Response: { user, token, limits: { used: 1, max: 5, isPremium: false } }

GET /api/auth/me
Headers: { Authorization: "Bearer <token>" }
Response: { user, limits: { used: 2, max: 5, isPremium: false } }
```

### QR Code Endpoints
```
POST /api/qr/generate
Headers: { Authorization: "Bearer <token>" } (optional)
Body: { url, size }
Response: { qrCode: { id, url, qrCodeUrl, size, createdAt }, limits: { used: 3, max: 5 } }

GET /api/qr/history
Headers: { Authorization: "Bearer <token>" } (optional)
Response: { qrCodes: [...], limits: { used: 3, max: 5 } }

DELETE /api/qr/:id
Headers: { Authorization: "Bearer <token>" }
Response: { success: true }
```

### Subscription Endpoints
```
POST /api/subscription/upgrade
Headers: { Authorization: "Bearer <token>" }
Body: { planType: "monthly" }
Response: { subscription: { id, planType, status, expiresAt }, limits: { used: 10, max: "unlimited" } }

GET /api/subscription/status
Headers: { Authorization: "Bearer <token>" }
Response: { subscription: { status, expiresAt }, limits: { used: 10, max: "unlimited" } }
```

## Database Models

### User Model
```javascript
{
  _id: ObjectId,
  email: String (unique),
  password: String (hashed),
  name: String,
  isPremium: Boolean (default: false),
  subscriptionExpiresAt: Date,
  qrCodeCount: Number (default: 0),
  createdAt: Date,
  updatedAt: Date
}
```

### QRCode Model
```javascript
{
  _id: ObjectId,
  userId: ObjectId (optional - for guests tracked by IP),
  guestIp: String (for non-authenticated users),
  url: String,
  qrCodeUrl: String,
  size: String,
  downloaded: Boolean (default: false),
  createdAt: Date
}
```

### Subscription Model
```javascript
{
  _id: ObjectId,
  userId: ObjectId,
  planType: String ("monthly"),
  status: String ("active", "expired", "cancelled"),
  startDate: Date,
  expiresAt: Date,
  createdAt: Date
}
```

## Frontend Changes Required

### Mock Data to Replace
1. `mockQRHistory` in `/frontend/src/data/mock.js` - Replace with API calls
2. Local state management - Add authentication context
3. QR generation logic - Connect to backend API with limits checking

### New Components to Add
1. **AuthModal** - Login/Register modal
2. **UserProfile** - Show current limits and subscription status  
3. **SubscriptionModal** - Upgrade to premium
4. **LimitReachedModal** - Show when limit is reached

### Frontend Integration Plan
1. **Add AuthContext** for user state management
2. **Modify QRGenerator** to check limits before generation
3. **Add authentication UI** in header
4. **Show current usage** (e.g., "2/5 QR codes used")
5. **Integrate subscription upgrade** when limits reached

## Backend Implementation Steps
1. **User authentication** with JWT
2. **Rate limiting middleware** based on user status
3. **QR code CRUD operations** with ownership tracking
4. **Subscription management** with expiration checking
5. **Guest user tracking** by IP address

## Security Considerations
- Rate limiting by IP for guests
- JWT token expiration and refresh
- Input validation for all endpoints
- Secure password hashing
- CORS configuration for production

## Error Handling
- 401: Unauthorized access
- 403: Limit exceeded
- 422: Validation errors
- 500: Server errors

All endpoints return consistent error format:
```javascript
{
  success: false,
  error: "Error message",
  code: "ERROR_CODE"
}
```