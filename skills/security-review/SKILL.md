---
name: security-review
description: Reviews application code and architecture for security vulnerabilities, insecure configurations, data exposure, authentication and authorization issues, dependency risks, and AI-specific security threats.
---

When reviewing an application for security:

1. Inspect the repository structure, application code, dependencies, configuration files, infrastructure, APIs, databases, and authentication mechanisms
2. Identify security-sensitive components and attack surfaces before reviewing individual files
3. Review the application following these security areas:

## Authentication

Check for:

- Missing authentication
- Weak authentication mechanisms
- Improper session handling
- Insecure token handling
- JWT vulnerabilities
- Missing token expiration
- Hardcoded credentials
- Credential leakage
- Weak password handling

## Authorization

Check for:

- Missing authorization checks
- Broken access control
- IDOR vulnerabilities
- Privilege escalation
- Missing resource ownership validation
- Tenant isolation failures
- Insecure role handling

Verify that authentication and authorization are treated as separate concerns.

## Input Validation

Check all external inputs, including:

- HTTP requests
- Query parameters
- Request bodies
- File uploads
- Headers
- Webhooks
- User-generated content
- Tool inputs
- LLM-generated parameters

Look for:

- SQL injection
- Command injection
- Path traversal
- SSRF
- XSS
- Unsafe deserialization
- Injection into downstream systems

Prefer validation at system boundaries.

## API Security

Review:

- Authentication
- Authorization
- Rate limiting
- Request validation
- CORS
- HTTP methods
- Error responses
- API versioning
- Sensitive endpoint exposure
- Excessive data returned by endpoints

Check whether internal functionality is accidentally exposed through public endpoints.

## Secrets & Configuration

Search for:

- API keys
- Passwords
- Tokens
- Private keys
- Database credentials
- Cloud credentials
- Secrets committed to source control
- Secrets inside Dockerfiles
- Secrets inside configuration files

Verify that secrets are loaded through environment variables or an appropriate secret-management mechanism.

Never reproduce discovered secrets in the final report.

## Database Security

Review:

- SQL queries
- ORM usage
- Database permissions
- Connection configuration
- Credential handling
- Input sanitization
- Row-level access controls
- Sensitive data storage

Check for SQL injection and excessive database privileges.

## Data Protection

Identify sensitive data handled by the application.

Review:

- Personal data
- Authentication data
- Financial data
- API credentials
- Internal business data
- AI conversation data
- Uploaded documents

Check:

- Encryption in transit
- Encryption at rest where appropriate
- Data minimization
- Access controls
- Logging of sensitive information
- Data retention

## Dependency Security

Inspect:

- `requirements.txt`
- `pyproject.toml`
- `package.json`
- Lock files
- Docker images
- Third-party services

Look for:

- Outdated dependencies
- Known vulnerabilities
- Unnecessary dependencies
- Untrusted packages
- Dependencies with excessive privileges

Do not claim a dependency is vulnerable unless evidence supports the claim.

## Infrastructure & Docker

Review:

- Dockerfiles
- Docker Compose
- Container permissions
- Exposed ports
- Mounted volumes
- Environment variables
- Network configuration
- Running as root
- Privileged containers

Check for unnecessary exposure of:

- Databases
- Redis
- Vector databases
- Internal APIs
- Admin interfaces

Prefer least privilege.

## Logging & Error Handling

Review whether errors or logs expose:

- Passwords
- API keys
- Tokens
- Personal data
- Database credentials
- Internal infrastructure
- Stack traces
- File paths

Verify that production errors do not reveal unnecessary implementation details.

## AI Security

For applications using LLMs, agents, RAG, or AI tools, additionally review:

### Prompt Injection

Check whether untrusted content can manipulate:

- System instructions
- Agent behavior
- Tool execution
- Retrieval behavior
- Output generation

### Tool Security

Review whether AI agents can:

- Execute arbitrary commands
- Access sensitive files
- Modify databases
- Send external requests
- Send messages
- Perform destructive actions

Verify that tools enforce their own authorization and validation.

Never rely exclusively on the LLM to enforce permissions.

### Data Exfiltration

Check whether prompts, retrieved documents, tool outputs, or model responses can expose sensitive information.

### RAG Security

Review:

- Document access control
- Metadata filtering
- Tenant isolation
- Unauthorized retrieval
- Document poisoning
- Prompt injection through documents
- Sensitive information leakage

### Model Output

Check whether model-generated output is trusted without validation.

AI-generated values must be treated as untrusted input when they interact with:

- Databases
- APIs
- Shell commands
- Files
- External services
- Application logic

## Webhook & External Integrations

Review:

- Webhook authentication
- Signature validation
- Replay protection
- Request validation
- External API credentials
- SSRF risks
- Timeout handling
- Rate limiting

Do not trust requests merely because they originate from an external service.

## Security Architecture

Identify the application's main attack surfaces.

Document:

- Entry points
- Trust boundaries
- Sensitive components
- External dependencies
- Data flows
- Privileged operations

When useful, create a Mermaid diagram showing the security boundaries.

Example:

```mermaid
flowchart TD
    Internet --> API
    API --> Auth
    Auth --> Application
    Application --> Database
    Application --> ExternalAPI
    Application --> LLM

    UntrustedInput --> API
    UntrustedInput --> LLM

    style Database stroke-width:2px
    style Auth stroke-width:2px