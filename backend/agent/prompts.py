"""
All LLM prompt templates for the Collaris agent.
Prompts are defined in CLAUDE.md §7.
Never put prompt strings inside node files — always import from here.
"""

RISK_NARRATIVE_PROMPT = """You are a prime brokerage risk analyst. Given the following portfolio data,
write a 2-sentence plain-English risk assessment.

Client: {client_name}
Strategy: {strategy}
MRS Score: {mrs}/100
Utilization: {utilization}%
Top Holdings: {holdings}
Trend: {trend}

Be direct. State the risk level and the primary driver. No jargon."""


MARGIN_CALL_MEMO_PROMPT = """You are a prime brokerage operations officer. Write a formal margin call notice.

Client: {client_name} ({client_id})
Shortfall: ${shortfall}M
Utilization: {utilization}%
Due By: {due_by}
Collateral Options: {recommendations}

Format: formal letter. Tone: professional, direct, urgent but not alarmist.
Include: the shortfall amount, deadline, and top 2 resolution options.
Max 200 words."""


COLLATERAL_RECOMMENDATION_PROMPT = """You are a collateral optimization specialist. Review the following collateral
portfolio and suggest the most efficient substitutions to resolve a margin shortfall.

Shortfall: ${shortfall}M
Available Unencumbered Assets: {assets}
Haircut Table: {haircuts}

Return a ranked list of up to 3 actions. For each: action description,
collateral freed ($M), and haircut impact. Be specific about asset names."""


ADVISORY_MEMO_PROMPT = """You are a prime brokerage coverage officer. Write a risk advisory memo.

Client: {client_name} ({client_id})
Strategy: {strategy}
MRS Score: {mrs}/100
Utilization: {utilization}%
Trend: {trend}
Lead Time to Breach: {lead_time} hours

Tone: proactive, analytical, constructive.
Content: current risk posture, trajectory, and 2-3 recommended actions.
Max 200 words."""
