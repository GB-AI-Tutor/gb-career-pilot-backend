# Security Policy

## 🔒 Reporting a Vulnerability

**Feel and Support** and the **GB Career Pilot** project take security seriously. We appreciate your efforts to responsibly disclose your findings.

### ⚠️ Please Do NOT:

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed
- Exploit the vulnerability beyond what is necessary to demonstrate it

### ✅ Please DO:

**Report security vulnerabilities to:** security@feelandsupport.org

Include the following in your report:

1. **Description** - Clear description of the vulnerability
2. **Impact** - Potential impact if exploited
3. **Steps to Reproduce** - Detailed steps to reproduce
4. **Proof of Concept** - Code/screenshots demonstrating the issue
5. **Suggested Fix** - If you have ideas for fixing it
6. **Your Contact** - How we can reach you for follow-up

## 📬 What to Expect

1. **Acknowledgment** - Within 48 hours
2. **Initial Assessment** - Within 1 week
3. **Regular Updates** - Every 7 days until resolved
4. **Resolution** - Target within 90 days (depending on severity)
5. **Credit** - You'll be credited in release notes (if desired)

## 🎯 Scope

### In Scope

- Backend API endpoints
- Authentication and authorization
- Data validation and sanitization
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Information disclosure
- Session management
- Rate limiting bypass
- Business logic vulnerabilities

### Out of Scope

- Issues in third-party services (Supabase, Vercel, etc.)
- Social engineering attacks
- Physical attacks
- Denial of Service (DoS/DDoS)
- Issues requiring physical access to servers
- Issues in deprecated endpoints/features

## 🏆 Recognition

We appreciate security researchers who help us keep GB Career Pilot secure!

### Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be:

1. ✅ Listed in our Security Hall of Fame (with permission)
2. ✅ Credited in release notes
3. ✅ Mentioned on our website
4. ✅ Given special Discord role
5. ✅ Provided recommendation letter (upon request)

**Note:** We currently don't have a bug bounty program, but we deeply appreciate your contributions!

## 🛡️ Security Best Practices

### For Contributors

When contributing code:

1. **Never commit secrets**
   - Use environment variables
   - Check .gitignore
   - Use .env.example templates

2. **Validate all inputs**
   - Use Pydantic models (backend)
   - Use Zod schemas (frontend)
   - Sanitize user input

3. **Use parameterized queries**
   - Never concatenate SQL queries
   - Use ORM features properly

4. **Implement proper authentication**
   - Use JWT tokens correctly
   - Implement proper session management
   - Check authorization on all protected routes

5. **Handle errors securely**
   - Don't expose stack traces to users
   - Log errors securely
   - Use generic error messages

6. **Keep dependencies updated**
   - Regularly update packages
   - Check for known vulnerabilities
   - Use `npm audit` and `pip-audit`

### For Users

1. **Use strong passwords**
2. **Enable two-factor authentication** (when available)
3. **Keep your account information private**
4. **Log out from shared computers**
5. **Report suspicious activity**

## 🔐 Security Features

### Current Implementation

- ✅ JWT-based authentication
- ✅ bcrypt password hashing (cost factor 12)
- ✅ Rate limiting (Redis-backed)
- ✅ CORS configuration
- ✅ Input validation (Pydantic + Zod)
- ✅ SQL injection protection (ORM)
- ✅ XSS protection (React auto-escaping)
- ✅ HTTPS in production
- ✅ Secure environment variable handling
- ✅ Error monitoring (Sentry)

### Planned Improvements

- [ ] Two-factor authentication
- [ ] Password reset functionality
- [ ] Account recovery
- [ ] Session management improvements
- [ ] Enhanced rate limiting
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] Regular security audits

## 📋 Security Checklist (For Reviewers)

When reviewing PRs, check for:

- [ ] No hardcoded secrets or credentials
- [ ] All inputs are validated
- [ ] Proper error handling (no info leakage)
- [ ] Authentication/authorization checks
- [ ] SQL queries are parameterized
- [ ] XSS protection in place
- [ ] CSRF protection (if needed)
- [ ] Rate limiting applied
- [ ] Logging doesn't expose sensitive data
- [ ] Dependencies are up to date

## 🔄 Security Update Policy

### Critical Vulnerabilities
- Patch released within 24-48 hours
- Emergency notification to all users
- Immediate deployment to production

### High Severity
- Patch released within 7 days
- Notification in release notes
- Scheduled deployment

### Medium/Low Severity
- Patch released in next regular update
- Mentioned in release notes
- Normal deployment schedule

## 📞 Contact

- **Security Issues:** security@feelandsupport.org
- **General Questions:** contact@feelandsupport.org
- **Discord:** Security channel (private, available to maintainers)

## 📖 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [React Security Best Practices](https://react.dev/learn/security)

---

## 🙏 Thank You

Thank you for helping keep GB Career Pilot and its users safe!

**Last Updated:** March 27, 2026
**Version:** 1.0

---

**Feel and Support** - Building Secure Technology for Students
