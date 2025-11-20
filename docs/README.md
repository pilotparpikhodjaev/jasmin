# Jasmin SMS Gateway - Documentation

Welcome to the Jasmin SMS Gateway documentation. This directory contains comprehensive documentation for the platform, organized by category.

## 📚 Documentation Structure

### [Architecture](architecture/)
System architecture, technical analysis, and service-specific design documentation.

- [System Analysis](architecture/system-analysis.md)
- [Technical Analysis](architecture/technical-analysis.md)
- [API Gateway Architecture](architecture/api-gateway-architecture.md)
- [Billing Service Architecture](architecture/billing-service-architecture.md)

### [Development Guides](guides/)
Development workflows, testing guides, and agent-based development patterns.

- [Agent Workflows](guides/agent-workflows.md)
- [Testing Documentation](guides/testing/)
  - [Test Credentials](guides/testing/test-credentials.md)
  - [OTP Testing](guides/testing/otp-testing.md)
  - [OTP Configuration](guides/testing/otp-configuration.md)

### [Implementation Plans](plans/)
Project plans, implementation checklists, and development prompts.

- [Implementation Plan](plans/implementation-plan.md)
- [Implementation Checklist](plans/implementation-checklist.md)
- [Project Plan](plans/project-plan.md)
- [Development Prompts](plans/prompts/)

### [Deployment](deployment/)
Infrastructure, deployment guides, and operational documentation.

- [Docker Guide](deployment/docker/docker-guide.md)
- [Helm Charts](deployment/helm/otp-platform.md)
- [Kubernetes Deployment](deployment/kubernetes/)

## 🚀 Quick Links

### Getting Started
- [Main README](../README.md) - Project overview
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute (if exists)
- [Code of Conduct](../CODE_OF_CONDUCT.md) - Community guidelines

### Development
- [CLAUDE.md](../CLAUDE.md) - AI assistant instructions
- [Development Guides](guides/) - Testing and workflows
- [Service Documentation](../services/) - Individual services

### Operations
- [Deployment Guides](deployment/) - Infrastructure and deployment
- [Security Policy](../SECURITY.md) - Security guidelines

## 🏗️ Service Documentation

Individual service documentation is located with each service:

- [API Gateway](../services/api-gateway/README.md)
- [Billing Service](../services/billing-service/README.md)
- [Routing Service](../services/routing-service/README.md)
- [Admin Web](../services/admin-web/README.md)
- [Client Web](../services/client-web/README.md)

## 📖 Documentation Standards

All documentation in this repository follows these standards:
- **Naming**: lowercase-with-dashes.md
- **Structure**: Each directory has a README.md index
- **Navigation**: Cross-references between related documents
- **Clarity**: Clear headings, table of contents for long documents

## 🤝 Contributing to Documentation

When contributing to documentation:
1. Follow the established folder structure
2. Update relevant README.md index files
3. Use consistent naming conventions
4. Add cross-references to related documents
5. Keep documentation close to code where appropriate

---

**Last Updated**: 2025-11-16
**Documentation Version**: 1.0
