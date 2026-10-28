"""
council.py — Multi-Agent Council (MoA-lite) for SIDIX
Runs multiple personas in parallel and synthesizes the results.
"""

from __future__ import annotations
import concurrent.futures
import logging
from typing import Any
from .agent_react import run_react, AgentSession

logger = logging.getLogger("sidix.council")

def run_council(
    question: str,
    personas: list[str] | None = None,
    *,
    lead_persona: str = "AYMAN",
    client_id: str = "",
    agency_id: str = "",
    conversation_id: str = "",
    allow_restricted: bool = False,
    max_steps: int | None = None,
) -> tuple[str, list[AgentSession]]:
    """
    Run a council of agents to answer a question.
    Returns (synthesized_answer, list_of_individual_sessions).
    """
    if personas is None:
        # Default diverse council
        personas = ["ABOO", "OOMAR", "ALEY"]
        
    logger.info(f"Council started for Q: '{question[:50]}...' with {personas}")
    
    sessions: list[AgentSession] = []
    
    # Step 1: Run agents in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(personas)) as executor:
        future_to_persona = {
            executor.submit(
                run_react,
                question=question,
                persona=p,
                client_id=client_id,
                agency_id=agency_id,
                conversation_id=conversation_id,
                allow_restricted=allow_restricted,
                max_steps=max_steps,
                verbose=False
            ): p
            for p in personas
        }
        
        for future in concurrent.futures.as_completed(future_to_persona):
            p = future_to_persona[future]
            try:
                session = future.result()
                sessions.append(session)
                logger.info(f"Agent {p} finished council task.")
            except Exception as e:
                logger.error(f"Agent {p} failed council task: {e}")

    if not sessions:
        return "Council failed to produce any answers.", []

    # Step 2: Synthesize answers using lead persona
    # Create a prompt for the lead persona to aggregate
    aggregation_prompt = (
        f"Anda adalah {lead_persona}, bertindak sebagai moderator Dewan SIDIX (Multi-Agent Council).\n"
        f"Pertanyaan user: {question}\n\n"
        "Berikut adalah jawaban dari beberapa agen spesialis:\n\n"
    )
    
    for i, s in enumerate(sessions, 1):
        aggregation_prompt += f"--- AGEN {s.persona} ---\n{s.final_answer}\n\n"
        
    aggregation_prompt += (
        "\nTugas Anda: Sintesiskan semua jawaban di atas menjadi satu jawaban yang komprehensif, "
        "seimbang, dan akurat. Jika ada perbedaan pendapat, sebutkan secara objektif. "
        "Tetap pertahankan gaya bahasa Anda yang bijak dan integratif."
    )
    
    # Run the lead agent to synthesize
    # We use a direct LLM call or a simple run_react with the new prompt
    try:
        # Use simple_mode to avoid lead agent doing its own tools unless needed
        synth_session = run_react(
            question=aggregation_prompt,
            persona=lead_persona,
            client_id=client_id,
            agency_id=agency_id,
            conversation_id=conversation_id,
            allow_restricted=allow_restricted,
            simple_mode=True 
        )
        final_answer = synth_session.final_answer
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        # Fallback synthesis: just concatenate
        final_answer = "Sintesis otomatis gagal. Berikut adalah rangkuman jawaban dewan:\n\n"
        for s in sessions:
            final_answer += f"### {s.persona}\n{s.final_answer}\n\n"

    return final_answer, sessions
