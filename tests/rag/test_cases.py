TEST_CASES = [
    # === REGISTRAR'S OFFICE ===
    {
        "query": "how do I request an enrollment verification letter",
        "relevant_keywords": ["enrollment verification", "registrar", "4 - 5 business days"],
        "expected_department": "Registrar's Office"
    },
    {
        "query": "I want to appeal my final grade",
        "relevant_keywords": ["final grade appeal", "registrar", "14 business days", "academic involvement"],
        "expected_department": "Registrar's Office"
    },
    {
        "query": "how long does it take to process a maximum course load request",
        "relevant_keywords": ["maximum course load", "2 business days", "enrollment"],
        "expected_department": "Registrar's Office"
    },
    {
        "query": "I need to take a leave of absence",
        "relevant_keywords": ["LOA", "student status", "3 - 5 business days", "registrar"],
        "expected_department": "Registrar's Office"
    },
    {
        "query": "how do I withdraw from Fulbright",
        "relevant_keywords": ["withdraw from Fulbright", "residential life", "billing", "5 - 14 business days"],
        "expected_department": "Registrar's Office"
    },
    {
        "query": "I need a student ID card",
        "relevant_keywords": ["student ID card", "15 business days", "registrar"],
        "expected_department": "Registrar's Office"
    },

    # === ACADEMIC AFFAIRS ===
    {
        "query": "how do I declare my major",
        "relevant_keywords": ["major declaration", "academic affairs", "minimum 15 days"],
        "expected_department": "Academic Affairs"
    },
    {
        "query": "I need a support letter for graduate school application",
        "relevant_keywords": ["letter of confirmation", "graduate school", "3 business days", "urgent"],
        "expected_department": "Academic Affairs"
    },
    {
        "query": "I want to apply for MOET course exemption",
        "relevant_keywords": ["MOET", "exemption", "2 business days", "academic affairs"],
        "expected_department": "Academic Affairs"
    },
    {
        "query": "I have a question about my capstone funding",
        "relevant_keywords": ["capstone", "funding", "minimum 15 days", "academic affairs"],
        "expected_department": "Academic Affairs"
    },

    # === CAREER SERVICES ===
    {
        "query": "I need help with my internship or experiential learning",
        "relevant_keywords": ["experiential learning", "career services", "EL"],
        "expected_department": "Career Services"
    },

    # === RESIDENTIAL LIFE ===
    {
        "query": "I want to change my room",
        "relevant_keywords": ["room change", "residential life", "case-by-case"],
        "expected_department": "Residential Life"
    },
    {
        "query": "how do I register my vehicle for parking",
        "relevant_keywords": ["parking slot", "vehicle registration", "5 working days", "residential life"],
        "expected_department": "Residential Life"
    },
    {
        "query": "I need a temporary residency confirmation paper",
        "relevant_keywords": ["temporary residency", "tạm trú", "20 working days", "residential life"],
        "expected_department": "Residential Life"
    },
    {
        "query": "something is broken in my apartment",
        "relevant_keywords": ["maintenance", "housing goods repair", "residential life", "facilities"],
        "expected_department": "Residential Life"
    },

    # === STUDENT FINANCIAL SERVICES ===
    {
        "query": "I have not received my meal allowance this month",
        "relevant_keywords": ["meal allowance", "allowances", "3 business days", "student financial services"],
        "expected_department": "Student Financial Services"
    },
    {
        "query": "how do I request a tuition fee refund",
        "relevant_keywords": ["recredit", "refund", "3 – 7 business days", "finance"],
        "expected_department": "Student Financial Services"
    },
    {
        "query": "I need to defer my tuition payment",
        "relevant_keywords": ["deferred payment", "extension request", "vice president", "billing"],
        "expected_department": "Student Financial Services"
    },
    {
        "query": "my scholarship has not been disbursed yet",
        "relevant_keywords": ["scholarship disbursement", "3 - 7 business days", "finance", "urgent"],
        "expected_department": "Student Financial Services"
    },
    {
        "query": "I need a VAT invoice",
        "relevant_keywords": ["VAT invoice", "5 – 7 business days", "finance"],
        "expected_department": "Student Financial Services"
    },

    # === STUDENT ENGAGEMENT ===
    {
        "query": "I want to register a new student club",
        "relevant_keywords": ["club registration", "7-15 business days", "student engagement", "senior manager"],
        "expected_department": "Student Engagement"
    },
    {
        "query": "how do I book the AV room",
        "relevant_keywords": ["AV room", "room booking", "3 - 5 business days", "student engagement"],
        "expected_department": "Student Engagement"
    },
    {
        "query": "I need help with reimbursement for my club event",
        "relevant_keywords": ["reimbursement", "3-4 business days", "student engagement", "operations and finance"],
        "expected_department": "Student Engagement"
    },

    # === WELLNESS ===
    {
        "query": "I want to book a counseling appointment",
        "relevant_keywords": ["counseling", "3 business days", "wellness", "booking"],
        "expected_department": "Wellness"
    },
    {
        "query": "I am feeling suicidal and need urgent help",
        "relevant_keywords": ["suicidal", "urgent", "1 business day", "wellness", "ISOS"],
        "expected_department": "Wellness"
    },
    {
        "query": "I need accessibility service for my learning plan",
        "relevant_keywords": ["accessibility service", "learning plan", "3 business days", "wellness"],
        "expected_department": "Wellness"
    },
    {
        "query": "I want to report harassment",
        "relevant_keywords": ["harassment", "wellness center", "residential life", "case-by-case"],
        "expected_department": "Residential Life"
    },
]
