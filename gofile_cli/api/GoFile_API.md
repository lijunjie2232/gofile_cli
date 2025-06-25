# Gofile API 集成指南

## 认证
- 所有请求必须包含以下认证头：
```http
Authorization: Bearer 您的_API_TOKEN
```

## 端点概览

### 上传文件
```http
POST https://upload.gofile.io/uploadfile
```
- 参数：
  - `file`（必需）- 要上传的文件
  - `folderId`（可选）- 目标文件夹ID

提供区域端点以优化性能。

### 文件夹管理
1. 创建文件夹：
```http
POST https://api.gofile.io/contents/createFolder
```
- 参数：
  - `parentFolderId`（必需）
  - `folderName`（可选）

2. 更新文件夹属性：
```http
PUT https://api.gofile.io/contents/{contentId}/update
```
- 可修改属性：名称、描述、标签、公开状态、过期时间、密码

### 内容管理
1. 删除内容：
```http
DELETE https://api.gofile.io/contents
```
- 参数：`contentsId`（逗号分隔的ID列表）

2. 获取内容信息：
```http
GET https://api.gofile.io/contents/{contentId}
```
- 可选：`password`（用于受保护内容的SHA-256哈希密码）

3. 搜索内容：
```http
GET https://api.gofile.io/contents/search
```
- 参数：`contentId`（搜索位置）、`searchedString`

### 直接链接
1. 创建直接链接：
```http
POST https://api.gofile.io/contents/{contentId}/directlinks
```
- 可配置限制：expireTime、sourceIpsAllowed、domainsAllowed、auth

2. 更新直接链接：
```http
PUT https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

3. 删除直接链接：
```http
DELETE https://api.gofile.io/contents/{contentId}/directlinks/{directLinkId}
```

### 内容操作
1. 复制内容：
```http
POST https://api.gofile.io/contents/copy
```
- 参数：`contentsId`、`folderId`

2. 移动内容：
```http
PUT https://api.gofile.io/contents/move
```
- 参数：`contentsId`、`folderId`

3. 导入公共内容：
```http
POST https://api.gofile.io/contents/import
```
- 参数：`contentsId`

### 账户管理
1. 获取账户ID：
```http
GET https://api.gofile.io/accounts/getid
```

2. 获取账户信息：
```http
GET https://api.gofile.io/accounts/{accountId}
```

3. 重置API令牌：
```http
POST https://api.gofile.io/accounts/{accountId}/resettoken
```

## 重要说明
- **高级账户要求**：大多数端点需要高级账户
- **速率限制**：按端点实施速率限制；过度使用可能导致IP被封禁
- **账户结构**：永久根文件夹作为所有内容的基础
- **数据删除**：DELETE操作是永久性的且不可逆
- **BETA状态**：API处于测试阶段，可能会发生变化；请定期查看文档更新