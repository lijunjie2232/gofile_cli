# Gofile API Integration Guide

## Authentication
- All requests must include the following authentication header:
```http
Authorization: Bearer your_api_token
```

## Endpoint Overview

### File Upload
```http
POST https://upload.gofile.io/uploadfile
```
- Parameters:
  - `file` (required) - The file to upload
  - `folderId` (optional) - Target folder ID

Regional endpoints are available for performance optimization.

### Folder Management
1. Create a folder:
```http
POST https://api.gofile.io/contents/createFolder
```
- Parameters:
  - `parentFolderId` (required)
  - `folderName` (optional)

2. Update folder attributes:
```http
PUT https://api.gofile.io/contents/{contentId}/update
```
- Updatable attributes: name, description, tags, public status, expiration time, password

### Content Management
1. Delete content:
```http
DELETE https://api.gofile.io/contents
```
- Parameter: `contentsId` (comma-separated list of IDs)

2. Get content information:
```http
GET https://api.gofile.io/contents/{contentId}
```
- Optional: `password` (SHA-256 hash password for protected content)

3. Search content:
```http
GET https://api.gofile.io/contents/search
```
- Parameters: `contentId` (search location), `searchedString`

### Direct Links
1. Create a direct link:
```http
POST https://api.gofile.io/contents/{contentId}/directlinks
```
- Configurable limits: expireTime, sourceIpsAllowed, domainsAllowed, auth

2. Update a direct link:
```http
PUT https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

3. Delete a direct link:
```http
DELETE https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

### Content Operations
1. Copy content:
```http
POST https://api.gofile.io/contents/copy
```
- Parameters: `contentsId`, `folderId`

2. Move content:
```http
PUT https://api.gofile.io/contents/move
```
- Parameters: `contentsId`, `folderId`

3. Import public content:
```http
POST https://api.gofile.io/contents/import
```
- Parameters: `contentsId`

### Account Management
1. Get account ID:
```http
GET https://api.gofile.io/accounts/getid
```

2. Get account information:
```http
GET https://api.gofile.io/accounts/{accountId}
```

3. Reset API token:
```http
POST https://api.gofile.io/accounts/{accountId}/resettoken
```

## Important Notes
- **Premium Account Requirement**: Most endpoints require a premium account
- **Rate Limiting**: Rate limits are applied per endpoint; excessive usage may result in IP blocking
- **Account Structure**: A permanent root folder serves as the base for all content
- **Data Deletion**: DELETE operations are permanent and irreversible
- **BETA Status**: The API is in beta testing and may change; please check for documentation updates regularly