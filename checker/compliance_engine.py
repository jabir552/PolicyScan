"""
Configurable Compliance Rules Engine for A2P 10DLC Privacy Policy and Terms of Service.
Implements detection logic, evidence extraction, and status determination (PASS, MISSING, NEEDS MANUAL REVIEW).
"""

import re
from typing import Dict, List, Any


def find_best_snippet(sentences: List[str], full_text: str, regex_pattern: str, max_length: int = 320) -> str:
    """Finds the most relevant sentence or text snippet matching the regex pattern."""
    compiled = re.compile(regex_pattern, re.IGNORECASE)
    
    # First attempt: search individual sentences
    for s in sentences:
        if compiled.search(s):
            return s.strip()[:max_length]
            
    # Second attempt: search in full text with sliding context window
    m = compiled.search(full_text)
    if m:
        start = max(0, m.start() - 60)
        end = min(len(full_text), m.end() + 100)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(full_text) else ""
        return f"{prefix}{full_text[start:end].strip()}{suffix}"
        
    return ""


# ---------------------------------------------------------------------------
# PRIVACY POLICY COMPLIANCE RULES
# ---------------------------------------------------------------------------

def check_pp_data_collection(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """
    Check 1: Disclosure of collected data and how it is used.
    Looks for statements detailing what information/data is collected and its purpose.
    """
    pattern_collect = r"(information\s+(we|that\s+we)\s+collect|what\s+data\s+(we|is)\s+collect|data\s+we\s+collect|types\s+of\s+information\s+collected|we\s+collect\s+(personal|information|data)|how\s+we\s+use\s+(your\s+)?(information|data)|use\s+of\s+(your\s+)?information|purpose\s+of\s+collection)"
    
    match = re.search(pattern_collect, text, re.IGNORECASE)
    if match:
        snippet = find_best_snippet(sentences, text, pattern_collect)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Identified clear data collection and usage disclosure sections."
        }
    
    # Fallback partial match for manual review
    if re.search(r"(collect|personal\s+data|information)", text, re.IGNORECASE) and re.search(r"(use|purpose|process)", text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, r"(collect|information|personal\s+data)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "General mentions of data and usage found, but standard disclosure headings were not clearly identified."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "No clear disclosure explaining what data is collected or how it is used was found."
    }


def check_pp_no_mobile_sharing(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """
    Check 2: Disclosure that mobile information and opt-in consent are not shared
    with third parties or affiliates for marketing or promotional purposes.
    """
    # Strict A2P 10DLC / Twilio required concepts:
    # (mobile / phone / text / sms / opt-in / messaging consent) +
    # (not shared / will not be shared / won't be shared / excluded / not sold) +
    # (third parties / affiliates / marketing / promotional)
    
    strict_patterns = [
        # Explicit Twilio exact/near-exact standard pattern
        r"exclude(s)?\s+text\s+messaging\s+originator\s+opt-?in\s+data\s+and\s+consent[;,]?\s+this\s+information\s+(won'?t|will\s+not)\s+be\s+shared",
        r"(mobile\s+information|phone\s+numbers?|text\s+messaging\s+(data|consent|opt-?in)|opt-?in\s+(data|consent))\s+(will\s+not|won'?t|is\s+not|are\s+not)\s+be\s+shared\s+with\s+(any\s+)?(third\s+parties|affiliates)",
        r"no\s+mobile\s+information\s+will\s+be\s+shared\s+with\s+third\s+parties(/affiliates|\s+or\s+affiliates)?\s+for\s+marketing",
        r"(not\s+share|never\s+share|will\s+not\s+sell|not\s+disclose)\s+.*?(mobile\s+number|phone\s+number|opt-?in|consent).*?(third\s+part|affiliate|marketing|promotional)",
        r"(mobile|phone|sms|text\s+messaging)\s+(information|data|consent)\s+.*?(not\s+be\s+shared|not\s+sold|never\s+shared).*?(third\s+part|affiliate)",
    ]

    for pat in strict_patterns:
        if re.search(pat, text, re.IGNORECASE):
            snippet = find_best_snippet(sentences, text, pat)
            return {
                "status": "PASS",
                "evidence": snippet,
                "explanation": "Found explicit disclosure that mobile information and opt-in consent are not shared with third parties or affiliates."
            }

    # Review case: Has third-party non-sharing, but might be missing explicit 'mobile/opt-in' or 'marketing/promotional' exclusion
    has_share_negation = re.search(r"(do\s+not\s+sell|will\s+not\s+share|not\s+share|never\s+share|not\s+disclose)\s+.*?third\s+part", text, re.IGNORECASE)
    has_mobile_mention = re.search(r"(mobile|phone|sms|text|opt-?in|messaging)", text, re.IGNORECASE)

    if has_share_negation and has_mobile_mention:
        snippet = find_best_snippet(sentences, text, r"(do\s+not\s+sell|will\s+not\s+share|not\s+share|never\s+share)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Found generic third-party non-sharing statement and mobile mentions, but requires verification that mobile opt-in data is specifically exempted from marketing/affiliate sharing."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing required statement guaranteeing mobile information and opt-in consent will not be shared with third parties/affiliates for marketing or promotional purposes."
    }


def check_pp_expected_consent_statement(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """
    Check 3: Detection of the expected text-messaging consent-data non-sharing statement.
    Specifically checks for the standard Twilio/carrier phrasing:
    'All the above categories exclude text messaging originator opt-in data and consent;
    this information won't be shared with any third parties.'
    """
    exact_pattern = r"exclude(s)?\s+text\s+messaging\s+originator\s+opt-?in\s+data\s+and\s+consent[;,]?\s+this\s+information\s+(won'?t|will\s+not)\s+be\s+shared(\s+with\s+any\s+third\s+parties)?"
    
    if re.search(exact_pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, exact_pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Detected the recommended Twilio standard text-messaging originator opt-in non-sharing statement."
        }

    # Near match variation
    variation_pattern = r"(text\s+messaging\s+originator\s+opt-?in\s+data|messaging\s+consent\s+data).*?(won'?t|will\s+not|not)\s+be\s+shared"
    if re.search(variation_pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, variation_pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Detected equivalent messaging originator consent-data non-sharing statement."
        }

    # Partial / review
    if re.search(r"originator\s+opt-?in|messaging\s+consent", text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, r"(originator\s+opt-?in|messaging\s+consent)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Found mention of originator opt-in/consent, but does not match standard safe-harbor phrasing."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Standard A2P 10DLC messaging consent data exclusion statement was not found."
    }


# ---------------------------------------------------------------------------
# TERMS OF SERVICE COMPLIANCE RULES
# ---------------------------------------------------------------------------

def check_tos_brand_name(text: str, sentences: List[str], title: str = "", **kwargs) -> Dict[str, Any]:
    """Check 1: Program or brand name identification."""
    pattern = r"(terms\s+of\s+(service|use)\s+for\s+([A-Za-z0-9\s,&]{2,30})|welcome\s+to\s+([A-Za-z0-9\s,&]{2,30})|these\s+terms.*?govern\s+your\s+use\s+of\s+([A-Za-z0-9\s,&]{2,30})|(\b[A-Za-z0-9\s,&]{2,30}\b)\s+(sms|text\s+messaging)\s+program)"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Identified brand/program identity defined in Terms of Service."
        }

    if title and len(title.strip()) > 2:
        return {
            "status": "PASS",
            "evidence": f"Page Title: {title}",
            "explanation": f"Brand/Service recognized from page title: '{title}'."
        }

    return {
        "status": "NEEDS MANUAL REVIEW",
        "evidence": "",
        "explanation": "Could not automatically identify the explicit brand or program name. Verify manually."
    }


def check_tos_program_description(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 2: Program description (explaining what types of messages users receive)."""
    pattern = r"(program\s+description|types?\s+of\s+(text\s+)?messages|messages?\s+include|you\s+may\s+receive\s+(text\s+messages|sms|notifications|alerts|updates|marketing|promotions)|our\s+sms\s+service\s+provides|used\s+to\s+send\s+you\s+(updates|alerts|account\s+notifications))"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Found description outlining the messaging program purpose."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing description of the SMS program or nature of messages sent."
    }


def check_tos_message_rates(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 3: Message and data rates disclosure ('Message and data rates may apply')."""
    pattern = r"(message\s+and\s+data\s+rates\s+may\s+apply|standard\s+message\s+and\s+data\s+rates\s+may\s+apply|msg\s*&\s*data\s+rates\s+may\s+apply|rates\s+may\s+apply\s+for\s+any\s+messages)"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Found standard message and data rates disclosure."
        }

    # Partial rates mention
    if re.search(r"(carrier|wireless)\s+charges|data\s+rates", text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, r"(carrier|wireless|data\s+rates)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Partial rate disclosure found. Twilio requires explicit 'Message and data rates may apply' wording."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing required 'Message and data rates may apply' disclosure."
    }


def check_tos_message_frequency(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 4: Message frequency or recurring-message disclosure."""
    pattern = r"(message\s+frequency\s+varies|recurring\s+messages?|message\s+frequency\s+may\s+vary|up\s+to\s+\d+\s+messages?\s+per|messages?\s+will\s+be\s+sent|frequency\s+of\s+messages|message\s+frequency)"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Found message frequency or recurring message disclosure."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing message frequency disclosure (e.g. 'Message frequency varies' or 'Recurring messages')."
    }


def check_tos_customer_support(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 5: Customer support contact information (email, phone, support URL)."""
    email_or_phone_pat = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|contact\s+(us|support)\s+at|customer\s+care|call\s+us\s+at)"
    
    # In context of support/help
    has_support_kw = re.search(r"(support|customer\s+(care|service)|help\s+desk|contact\s+us)", text, re.IGNORECASE)
    has_contact = re.search(email_or_phone_pat, text, re.IGNORECASE)

    if has_support_kw and has_contact:
        snippet = find_best_snippet(sentences, text, r"(support|customer\s+(care|service)|contact\s+us)")
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Customer support contact details (phone, email, or help link) identified."
        }

    if has_support_kw:
        snippet = find_best_snippet(sentences, text, r"(support|customer\s+(care|service)|contact)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Support section mentioned, but explicit email or phone number was not unambiguously detected."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing customer support contact information (phone number, email, or direct contact link)."
    }


def check_tos_stop_instructions(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 6: STOP opt-out instructions."""
    pattern = r"(reply\s+STOP(\s+to\s+cancel|\s+to\s+unsubscribe|\s+to\s+opt-?out)?|text\s+STOP|opt-?out\s+by\s+replying\s+STOP|send\s+STOP|type\s+STOP)"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Detected clear opt-out instructions referencing STOP keyword."
        }

    if re.search(r"\bSTOP\b", text):
        snippet = find_best_snippet(sentences, text, r"\bSTOP\b")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Found keyword 'STOP', but context could not confirm explicit opt-out instruction."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing required opt-out instruction (e.g. 'Text STOP to cancel')."
    }


def check_tos_help_instructions(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 7: HELP instructions."""
    pattern = r"(reply(\s+with\s+(the\s+)?keyword)?\s+HELP|text\s+HELP|send\s+HELP|type\s+HELP|for\s+help\s+reply\s+HELP|HELP\s+for\s+(more\s+)?(help|assistance|info))"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Detected instructions referencing HELP keyword."
        }

    if re.search(r"\bHELP\b", text):
        snippet = find_best_snippet(sentences, text, r"\bHELP\b")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Found keyword 'HELP', but sentence structure requires manual confirmation."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing required assistance instruction (e.g. 'Text HELP for help')."
    }


def check_tos_bold_stop_help(bold_texts: List[str], text: str, **kwargs) -> Dict[str, Any]:
    """Check 8: STOP and HELP instructions displayed in bold."""
    bold_combined = " ".join(bold_texts)
    has_bold_stop = bool(re.search(r"\bSTOP\b", bold_combined))
    has_bold_help = bool(re.search(r"\bHELP\b", bold_combined))

    if has_bold_stop and has_bold_help:
        snippets = [t for t in bold_texts if re.search(r"\b(STOP|HELP)\b", t)]
        return {
            "status": "PASS",
            "evidence": " | ".join(snippets[:3]),
            "explanation": "Both STOP and HELP keywords were verified inside HTML bold/strong elements."
        }

    if has_bold_stop or has_bold_help:
        which = "STOP" if has_bold_stop else "HELP"
        missing = "HELP" if has_bold_stop else "STOP"
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": f"Found bold: {which}, but {missing} was not confirmed bold in HTML tags.",
            "explanation": f"Twilio guidelines state both STOP and HELP must be displayed in bold. Only {which} was found bold."
        }

    # If neither found bold, but both appear in plain text
    if re.search(r"\bSTOP\b", text) and re.search(r"\bHELP\b", text):
        return {
            "status": "MISSING",
            "evidence": "Keywords exist in body text, but were not enclosed in <b>, <strong>, or CSS bold tags.",
            "explanation": "STOP and HELP keywords exist in text but are NOT displayed in bold font as required by Twilio/carriers."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Neither STOP nor HELP were found in bold format."
    }


def check_tos_privacy_policy_link(links: List[Dict[str, str]], text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 9: Link to the privacy policy included in the Terms of Service."""
    # Check hyperlinks
    for lk in links:
        href = lk.get("href", "").lower()
        anchor = lk.get("text", "").lower()
        if "privacy" in href or "privacy" in anchor:
            return {
                "status": "PASS",
                "evidence": f"Anchor: '{lk.get('text')}' -> Link: '{lk.get('href')}'",
                "explanation": "Found clickable hyperlink directing to the Privacy Policy."
            }

    # If no <a> tag, check if full privacy URL or mention is typed in text
    pattern = r"(privacy\s+policy(\s+is\s+available\s+at|\s+at|\s*:)?\s*(https?://[^\s]+)?)"
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Privacy policy is referenced in text, but active hyperlink <a> tag was not detected."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Terms of Service must include a direct link to the Privacy Policy."
    }


def check_tos_carrier_disclaimer(text: str, sentences: List[str], **kwargs) -> Dict[str, Any]:
    """Check 10: Carrier disclaimer ('Carriers are not liable for delayed or undelivered messages')."""
    pattern = r"(carriers?\s+(are|is)\s+not\s+(liable|responsible)\s+for\s+(any\s+)?(delayed\s+or\s+undelivered|delayed|late|undelivered|dropped)\s+messages?|t-mobile\s+and\s+other\s+carriers\s+are\s+not\s+liable|wireless\s+carriers\s+are\s+not\s+liable)"
    
    if re.search(pattern, text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, pattern)
        return {
            "status": "PASS",
            "evidence": snippet,
            "explanation": "Found standard carrier non-liability disclaimer."
        }

    if re.search(r"carriers?\s+.*?(not\s+liable|not\s+responsible)", text, re.IGNORECASE):
        snippet = find_best_snippet(sentences, text, r"carriers?\s+.*?(not\s+liable|not\s+responsible)")
        return {
            "status": "NEEDS MANUAL REVIEW",
            "evidence": snippet,
            "explanation": "Carrier liability disclaimer mentioned, but phrasing differs from standard wording."
        }

    return {
        "status": "MISSING",
        "evidence": "",
        "explanation": "Missing required carrier disclaimer: 'Carriers are not liable for any delayed or undelivered messages'."
    }


# ---------------------------------------------------------------------------
# RULES REGISTRY
# ---------------------------------------------------------------------------

PRIVACY_POLICY_RULES = [
    {
        "rule_id": "PP-01",
        "title": "Data Collection & Use Disclosure",
        "description": "Disclose what data you collect and how it's used.",
        "checker_func": check_pp_data_collection,
    },
    {
        "rule_id": "PP-02",
        "title": "Mobile Information Non-Sharing Statement",
        "description": "Explain that mobile information and opt-in consent won't be shared with third parties or affiliates for marketing or promotional purposes.",
        "checker_func": check_pp_no_mobile_sharing,
    },
    {
        "rule_id": "PP-03",
        "title": "Expected Messaging Consent Safe-Harbor Language",
        "description": "Twilio recommended clause: 'All the above categories exclude text messaging originator opt-in data and consent; this information won't be shared with any third parties.'",
        "checker_func": check_pp_expected_consent_statement,
    },
]

TOS_RULES = [
    {
        "rule_id": "TOS-01",
        "title": "Program or Brand Name",
        "description": "Explicit identification of the brand or messaging program name.",
        "checker_func": check_tos_brand_name,
    },
    {
        "rule_id": "TOS-02",
        "title": "Program Description",
        "description": "Description explaining the purpose and types of messages users will receive.",
        "checker_func": check_tos_program_description,
    },
    {
        "rule_id": "TOS-03",
        "title": "Message and Data Rates Disclosure",
        "description": "Statement that 'Message and data rates may apply'.",
        "checker_func": check_tos_message_rates,
    },
    {
        "rule_id": "TOS-04",
        "title": "Message Frequency Disclosure",
        "description": "Disclosure that 'Message frequency varies' or recurring message notification.",
        "checker_func": check_tos_message_frequency,
    },
    {
        "rule_id": "TOS-05",
        "title": "Customer Support Contact Information",
        "description": "Customer care contact information including email, phone, or support URL.",
        "checker_func": check_tos_customer_support,
    },
    {
        "rule_id": "TOS-06",
        "title": "STOP Opt-Out Instructions",
        "description": "Instructions explaining how to opt out (e.g., 'Reply STOP to cancel').",
        "checker_func": check_tos_stop_instructions,
    },
    {
        "rule_id": "TOS-07",
        "title": "HELP Assistance Instructions",
        "description": "Instructions explaining how to get assistance (e.g., 'Reply HELP for help').",
        "checker_func": check_tos_help_instructions,
    },
    {
        "rule_id": "TOS-08",
        "title": "STOP and HELP Displayed in Bold",
        "description": "Both HELP and STOP opt-out instructions must be displayed in bold formatting.",
        "checker_func": check_tos_bold_stop_help,
    },
    {
        "rule_id": "TOS-09",
        "title": "Link to Privacy Policy",
        "description": "Direct, accessible link to the company's Privacy Policy.",
        "checker_func": check_tos_privacy_policy_link,
    },
    {
        "rule_id": "TOS-10",
        "title": "Carrier Non-Liability Disclaimer",
        "description": "Disclosure stating that 'Carriers are not liable for any delayed or undelivered messages'.",
        "checker_func": check_tos_carrier_disclaimer,
    },
]


def evaluate_privacy_policy(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluates all Privacy Policy compliance rules against parsed page data."""
    results = []
    text = page_data.get("text", "")
    sentences = page_data.get("sentences", [])
    title = page_data.get("title", "")
    bold_texts = page_data.get("bold_texts", [])
    links = page_data.get("links", [])

    for r in PRIVACY_POLICY_RULES:
        check_out = r["checker_func"](
            text=text,
            sentences=sentences,
            title=title,
            bold_texts=bold_texts,
            links=links
        )
        results.append({
            "document_type": "Privacy Policy",
            "rule_id": r["rule_id"],
            "requirement_title": r["title"],
            "description": r["description"],
            "status": check_out.get("status", "MISSING"),
            "evidence_snippet": check_out.get("evidence", ""),
            "explanation": check_out.get("explanation", ""),
        })
    return results


def evaluate_terms_of_service(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluates all Terms of Service compliance rules against parsed page data."""
    results = []
    text = page_data.get("text", "")
    sentences = page_data.get("sentences", [])
    title = page_data.get("title", "")
    bold_texts = page_data.get("bold_texts", [])
    links = page_data.get("links", [])

    for r in TOS_RULES:
        check_out = r["checker_func"](
            text=text,
            sentences=sentences,
            title=title,
            bold_texts=bold_texts,
            links=links
        )
        results.append({
            "document_type": "Terms of Service",
            "rule_id": r["rule_id"],
            "requirement_title": r["title"],
            "description": r["description"],
            "status": check_out.get("status", "MISSING"),
            "evidence_snippet": check_out.get("evidence", ""),
            "explanation": check_out.get("explanation", ""),
        })
    return results
