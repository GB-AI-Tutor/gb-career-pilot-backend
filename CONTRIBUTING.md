# Contributing to GB Career Pilot

First off, thank you for considering contributing to GB Career Pilot! 🎉

We're a student-led open source project under **Feel and Support** organization, and we love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🌟 Our Mission

**Feel and Support** aims to empower Pakistani students with AI-powered career guidance. Every contribution helps thousands of students make better educational decisions!

## 🚀 Getting Started

### Join Our Community

1. **Join our Discord:** [Your Discord Invite Link]
2. **Introduce yourself** in `#introductions`
3. **Check out** `#project-overview` to understand the project
4. **Browse** `#good-first-issues` for beginner-friendly tasks

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork:
   git clone https://github.com/YOUR_USERNAME/gb-career-pilot.git
   cd gb-career-pilot
   ```

2. **Backend Setup**
   ```bash
   cd gb-career-pilot-backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   uvicorn src.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd gb-career-pilot-frontend
   npm install
   cp .env.example .env
   # Edit .env with your API URL
   npm run dev
   ```

4. **Read the documentation**
   - `PROJECT_STATUS_COMPLETE.md` - Complete project overview
   - `COMPLETE_TECH_STACK.md` - Tech stack details
   - `README.md` - Quick start guide

## 📋 How to Contribute

### 1. Pick an Issue

- **Beginners:** Look for issues labeled `good first issue` or `beginner-friendly`
- **Intermediate:** Check `help wanted` or `enhancement` labels
- **Advanced:** Tackle `feature` or `architecture` issues

**No issue for what you want to do?** Create one! Discuss it first in Discord or GitHub Issues.

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding tests

### 3. Make Your Changes

- **Write clean code** - Follow existing code style
- **Add comments** - Especially for complex logic
- **Test your changes** - Make sure everything works
- **Update docs** - If you change functionality

### 4. Commit Your Changes

We follow **Conventional Commits** format:

```bash
# Format: <type>(<scope>): <description>
git commit -m "feat(ai-chat): add conversation history export"
git commit -m "fix(auth): resolve JWT token expiration issue"
git commit -m "docs(readme): add Docker setup instructions"
```

**Commit types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting, no logic change)
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Then create a Pull Request on GitHub
```

**Pull Request Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested locally
- [ ] Added/updated tests
- [ ] All tests pass

## Screenshots (if applicable)

## Checklist
- [ ] Code follows project style
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
```

## 🎯 Contribution Areas

### 1. **Frontend Development** (React, Tailwind)
- UI/UX improvements
- New pages/components
- Responsive design fixes
- Accessibility improvements
- Animation enhancements

**Skills needed:** JavaScript, React, CSS, HTML

### 2. **Backend Development** (Python, FastAPI)
- API endpoints
- Database optimizations
- AI prompt engineering
- Authentication improvements
- Rate limiting enhancements

**Skills needed:** Python, FastAPI, SQL, REST APIs

### 3. **AI/ML Enhancement**
- Improve AI prompts
- Add RAG (Retrieval Augmented Generation)
- Fine-tune responses
- Add new AI features
- Context management

**Skills needed:** Python, LangChain, Prompt Engineering

### 4. **Database & Data**
- Add more universities
- Enrich program data
- Database optimizations
- Data validation
- Schema improvements

**Skills needed:** SQL, PostgreSQL, Data Entry

### 5. **DevOps & Infrastructure**
- CI/CD improvements
- Docker optimizations
- Monitoring setup
- Performance optimization
- Security hardening

**Skills needed:** Docker, CI/CD, Linux, Cloud Platforms

### 6. **Documentation**
- Improve README
- Write tutorials
- Create video guides
- API documentation
- Translation (Urdu support!)

**Skills needed:** Technical Writing, Markdown

### 7. **Testing**
- Unit tests
- Integration tests
- End-to-end tests
- Performance tests
- Security tests

**Skills needed:** pytest, Vitest, Testing Best Practices

### 8. **Design**
- UI mockups
- Brand assets
- Icons and illustrations
- User flow diagrams
- Marketing materials

**Skills needed:** Figma, Adobe XD, Graphic Design

## 🏆 Recognition

We value every contribution! Contributors will be:

- ✅ Listed in `CONTRIBUTORS.md`
- ✅ Mentioned in release notes
- ✅ Given Discord roles based on contributions
- ✅ Featured on Feel and Support website
- ✅ Provided recommendation letters (upon request)
- ✅ Invited to team meetings and decision-making

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability
- Ethnicity, gender identity and expression
- Level of experience, education
- Nationality, personal appearance
- Race, religion, sexual orientation

### Our Standards

**Positive behavior:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community
- ✅ Showing empathy towards others

**Unacceptable behavior:**
- ❌ Trolling, insulting/derogatory comments
- ❌ Personal or political attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Unprofessional conduct

### Enforcement

Violations can be reported to [conduct@feelandsupport.org]. All complaints will be reviewed and investigated.

## 🎓 Learning Resources

### For Beginners

**Git & GitHub:**
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [First Contributions](https://github.com/firstcontributions/first-contributions)

**Python/FastAPI:**
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Python for Beginners](https://www.python.org/about/gettingstarted/)

**React:**
- [React Official Tutorial](https://react.dev/learn)
- [Vite Guide](https://vitejs.dev/guide/)

**Ask for help** in Discord `#help` channel!

## 💬 Communication Channels

- **Discord:** Main communication hub
  - `#general` - General discussion
  - `#help` - Get help with setup or issues
  - `#showcase` - Show your work
  - `#ideas` - Feature ideas and discussions
  - `#code-review` - Request code reviews

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Long-form discussions
- **Email:** [contact@feelandsupport.org]

## 🚦 Pull Request Process

1. **Create PR** with clear description
2. **Wait for review** (usually within 48 hours)
3. **Address feedback** from reviewers
4. **Get approval** from at least 2 maintainers
5. **Merge!** 🎉

### Review Criteria

Reviewers will check:
- ✅ Code quality and style
- ✅ Test coverage
- ✅ Documentation updates
- ✅ No breaking changes
- ✅ Security implications
- ✅ Performance impact

## 🎯 Roadmap & Feature Requests

See our [ROADMAP.md](./ROADMAP.md) for planned features.

Want to suggest a feature?
1. Check existing issues
2. Create a new issue with `feature` label
3. Discuss in Discord `#ideas`
4. Get community feedback
5. Start working if approved!

## 🐛 Bug Reports

**Before reporting:**
- Search existing issues
- Try latest version
- Check documentation

**Good bug report includes:**
- Clear title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/logs
- Environment (OS, browser, versions)

## ❓ Questions?

- **Setup issues?** → Discord `#help`
- **Feature ideas?** → Discord `#ideas` or GitHub Discussions
- **Bug found?** → GitHub Issues
- **Security issue?** → Email [security@feelandsupport.org]
- **General questions?** → Discord `#general`

## 🌍 Internationalization

We welcome translations!
- Urdu translation highly appreciated
- Arabic, Bengali, Hindi also welcome
- See `i18n` folder for translation files

## 📝 License

By contributing, you agree that your contributions will be licensed under the project's dual-license:
- **Free** for non-profit use
- **Commercial license required** for commercial use

See [LICENSE.md](./LICENSE.md) for details.

---

## 🙏 Thank You!

Every contribution, no matter how small, makes a difference. Together, we're empowering students to make better educational choices!

**Happy Contributing!** 🚀

---

**Feel and Support** - Empowering Students Through Technology

*For more information, visit our website or join our Discord community!*
