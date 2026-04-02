const API_BASE = "";

function formatJson(data) {
    return JSON.stringify(data, null, 2);
}

function getInputValue(sectionContent, field) {
    const input = sectionContent.querySelector(
        `.input-field[data-var="${field}"]`,
    );
    return input ? input.value : "";
}

function interpolateEndpoint(endpoint, userId, sectionContent) {
    let result = endpoint;
    result = result.replace(/\{\{user_id\}\}/g, userId);
    result = result.replace(
        /\{\{email_id\}\}/g,
        getInputValue(sectionContent, "email_id"),
    );
    result = result.replace(
        /\{\{draft_id\}\}/g,
        getInputValue(sectionContent, "draft_id"),
    );
    result = result.replace(
        /\{\{thread_id\}\}/g,
        getInputValue(sectionContent, "thread_id"),
    );
    return result;
}

function interpolateBody(body, userId, sectionContent) {
    if (!body) return body;
    let result = body;
    result = result.replace(/\{\{user_id\}\}/g, userId);
    result = result.replace(
        /\{\{email\}\}/g,
        getInputValue(sectionContent, "email"),
    );
    result = result.replace(
        /\{\{password\}\}/g,
        getInputValue(sectionContent, "password"),
    );
    result = result.replace(
        /\{\{username\}\}/g,
        getInputValue(sectionContent, "username"),
    );
    result = result.replace(
        /\{\{email_id\}\}/g,
        getInputValue(sectionContent, "email_id"),
    );
    result = result.replace(
        /\{\{recipient_email\}\}/g,
        getInputValue(sectionContent, "recipient_email"),
    );
    result = result.replace(
        /\{\{subject\}\}/g,
        getInputValue(sectionContent, "subject"),
    );
    result = result.replace(
        /\{\{body\}\}/g,
        getInputValue(sectionContent, "body"),
    );
    result = result.replace(
        /\{\{draft_id\}\}/g,
        getInputValue(sectionContent, "draft_id"),
    );
    result = result.replace(
        /\{\{thread_id\}\}/g,
        getInputValue(sectionContent, "thread_id"),
    );
    result = result.replace(
        /\{\{context\}\}/g,
        getInputValue(sectionContent, "context"),
    );
    result = result.replace(
        /\{\{date\}\}/g,
        getInputValue(sectionContent, "date"),
    );
    result = result.replace(
        /\{\{time\}\}/g,
        getInputValue(sectionContent, "time"),
    );
    result = result.replace(
        /\{\{message\}\}/g,
        getInputValue(sectionContent, "message"),
    );
    return result;
}

async function callApi(endpoint, options = {}) {
    const startTime = Date.now();
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
            ...options,
        });

        const elapsed = Date.now() - startTime;
        const contentType = response.headers.get("content-type") || "";

        let data;
        let isJson = contentType.includes("application/json");

        if (isJson) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        const result = {
            status: response.status,
            statusText: response.statusText,
            time: `${elapsed}ms`,
            data: data,
        };

        return result;
    } catch (error) {
        return {
            status: 0,
            statusText: "Error",
            time: `${Date.now() - startTime}ms`,
            error: error.message,
        };
    }
}

function displayResponse(result) {
    const output = document.getElementById("response-output");
    const statusColor =
        result.status >= 200 && result.status < 300 ? "#10b981" : "#ef4444";

    output.innerHTML = `<span style="color: ${statusColor}">${result.status} ${result.statusText}</span> (${result.time})\n\n${formatJson(result.data || result.error)}`;
}

function displayError(error) {
    const output = document.getElementById("response-output");
    output.innerHTML = `<span style="color: #ef4444">Error</span>\n\n${error}`;
}

async function checkAgentStatus() {
    const indicator = document.getElementById("agent-status-indicator");
    const text = document.getElementById("agent-status-text");

    try {
        const result = await callApi("/api/agent/health");
        if (result.status === 200 && result.data.status === "online") {
            indicator.className = "status-indicator online";
            text.textContent = "Agent: Online";
        } else {
            indicator.className = "status-indicator offline";
            text.textContent = "Agent: Offline";
        }
    } catch (e) {
        indicator.className = "status-indicator offline";
        text.textContent = "Agent: Offline";
    }
}

async function loadUsers() {
    const select = document.getElementById("user-select");
    select.innerHTML = '<option value="">Loading...</option>';

    try {
        const result = await callApi("/api/auth/users");

        if (result.status >= 200 && result.status < 300 && result.data.users) {
            const users = result.data.users;
            if (users.length === 0) {
                select.innerHTML = '<option value="">No users found</option>';
            } else {
                select.innerHTML = users
                    .map(
                        (u) =>
                            `<option value="${u.id}">${u.username} (${u.email})</option>`,
                    )
                    .join("");
                
                // Auto-select first user and fill fields
                select.selectedIndex = 0;
                if (select.value) {
                    select.dispatchEvent(new Event("change"));
                }
            }
        } else {
            select.innerHTML = '<option value="">Error loading users</option>';
        }
    } catch (error) {
        select.innerHTML = '<option value="">Error loading users</option>';
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
    checkAgentStatus();

    setInterval(checkAgentStatus, 30000);

    document.getElementById("refresh-users").addEventListener("click", () => {
        loadUsers();
    });

    document
        .getElementById("user-select")
        .addEventListener("change", async (event) => {
            const userId = event.target.value;
            if (!userId) return;

            const result = await callApi(`/api/auth/users/${userId}`);

            if (result.status === 200 && result.data && result.data.user) {
                const user = result.data.user;

                const authTab = document.getElementById("auth-tab");
                if (!authTab) return;

                const inputs = authTab.querySelectorAll(".input-field");

                if (inputs.length >= 6) {
                    inputs[3].value = user.username;
                    inputs[4].value = user.email;
                }
            }
        });

    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document
                .querySelectorAll(".tab-btn")
                .forEach((b) => b.classList.remove("active"));
            document
                .querySelectorAll(".tab-pane")
                .forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document
                .getElementById(`${btn.dataset.tab}-tab`)
                .classList.add("active");
        });
    });

    document.querySelectorAll(".section-title").forEach((title) => {
        title.addEventListener("click", () => {
            title.classList.toggle("collapsed");
            const content = title.nextElementSibling;
            content.classList.toggle("hidden");
        });
    });

    document.querySelectorAll(".test-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const method = btn.dataset.method;
            let endpoint = btn.dataset.endpoint;
            let body = btn.dataset.body;

            const userSelect = document.getElementById("user-select");
            const userId = userSelect.value;

            if (endpoint === "/api/agent/health") {
                const result = await callApi(endpoint);
                displayResponse(result);
                return;
            }

            if (!userId && endpoint.includes("{{user_id}}")) {
                displayError("Please select a user first");
                return;
            }

            const sectionContent = btn.closest(".section-content");

            endpoint = interpolateEndpoint(endpoint, userId, sectionContent);
            body = interpolateBody(body, userId, sectionContent);

            const options = { method };
            if (body && method !== "GET") {
                options.body = body;
            }

            displayResponse({
                status: "...",
                statusText: "Loading",
                time: "...",
                data: { loading: true },
            });

            const result = await callApi(endpoint, options);
            displayResponse(result);

            if (result.status >= 200 && result.status < 300) {
                if (
                    endpoint === "/api/auth/signup" ||
                    (endpoint.includes("/api/auth/users/") &&
                        (method === "PUT" || method === "DELETE"))
                ) {
                    loadUsers();
                }
            }
        });
    });

    document.getElementById("clear-response").addEventListener("click", () => {
        document.getElementById("response-output").textContent = "";
    });
});
