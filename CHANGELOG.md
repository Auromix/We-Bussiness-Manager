# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modern Python packaging with `pyproject.toml` and `pip install` support
- Comprehensive README with bilingual documentation (English + Chinese)
- GitHub community files (CODE_OF_CONDUCT, SECURITY, CONTRIBUTING)
- CI/CD workflow with multi-version Python testing

## [0.1.0] - 2025-02-18

### Added
- **Agent Module**: Multi-LLM agent framework with function calling
  - Support for OpenAI, Claude, MiniMax, and OpenAI-compatible open-source models
  - Strategy pattern for transparent provider switching
  - Function registry with auto-discovery and type inference
  - Multi-turn tool calling with `tool_call_id` tracking
  - `provider_extras` passthrough for Anthropic-style context preservation
- **Database Module**: Repository-pattern ORM layer
  - Entity repositories: Staff, Customer, ServiceType, Product, Channel
  - Business repositories: ServiceRecord, ProductSale, Membership
  - System repositories: Message, Summary, Plugin
  - `DatabaseManager` facade for unified access
  - SQLite and PostgreSQL support
- **Interface Module**: Multi-channel user interaction
  - `WebChannel`: FastAPI-based web dashboard with chat + data visualization
  - `TerminalChannel`: CLI-based interaction for development
  - `ChannelManager`: Unified multi-channel management
- **Config Module**: Pluggable business configuration
  - `BusinessConfig` abstract base class for custom business types
  - Default `TherapyStoreConfig` (massage/wellness clinic)
  - Dynamic LLM system prompt generation from business config
  - 30+ registered business functions for Agent tool calling
- **Web Dashboard**: Full-featured management UI
  - AI chat assistant with natural language business operations
  - Database visualization and data browsing
  - JWT-based authentication
- **Examples**: Comprehensive usage examples
  - Agent examples (basic, advanced, function calling, provider switching)
  - Database examples (CRUD, business repos, entity repos, system repos)
  - Full integration example (therapy clinic management)

[Unreleased]: https://github.com/Auromix/bizbot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Auromix/bizbot/releases/tag/v0.1.0


