# Manual End-to-End Verification Log

## 1. Test Notification Workflow
- **Action**: Sent a POST request to `/onboard_client` with dummy client details.
- **Result**: The endpoint returned `200 OK`. Verified the local SMTP log (via printed `[Notifications] Email sent to...`) and confirmed that a new record was added to the `email_logs` table in the database containing the client's name and onboarding details.

## 2. Test PDF Report Workflow
- **Action**: Created a test client and portfolio. Sent a POST request to `/reports` with the `client_id`.
- **Result**: Response included a valid URL (`/static/reports/report_X_Y.pdf`). Downloaded the PDF successfully from the `static/reports/` directory; it opened correctly and rendered the portfolio table. 
- **Action (Edge Case)**: Sent a POST request to `/reports` for a new client with zero holdings.
- **Result**: API handled it gracefully, returning a `400 Bad Request` with the message "No holdings available to generate report," avoiding division-by-zero crashes.

## 3. Test Client Portal Workflow
- **Action**: Logged in as a test client and navigated to the dashboard via `/my/dashboard/analytics`.
- **Result**: The client portal rendered correctly with KPI cards, holdings, and goals populated.
- **Action**: Logged in as the client's assigned advisor and previewed the portal.
- **Result**: Advisor successfully viewed the data.
- **Action (IDOR Check)**: Logged in as a different advisor and attempted to fetch the first advisor's client's dashboard.
- **Result**: API returned `403 Forbidden`, confirming the IDOR vulnerability is fixed and unauthorized preview access is blocked.

**Conclusion**: All workflows (Notifications, PDF Generation, and Portal Security) pass manual end-to-end verification.
