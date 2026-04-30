# 13 — CORE ALGORITHMS

## Jiwa · Raudah · Jariyah · CQF · Nafs · Sanad · Naskh

**Version:** 1.0 **Date:** 2026-04-25 **Classification:** ALGORITHMIC
FOUNDATION

------------------------------------------------------------------------

## 1. JIWA ORCHESTRATOR ALGORITHM

### 1.1 Master Orchestration Flow

`async`` ``def`` jiwa_orchestrate(request: ``dict``) ``->`` ``dict``:`\
`    ``"""`\
`    Master orchestration algorithm for SIDIX.`\
`    Coordinates all 7 pillars for every request.`\
`    """`\
`    start_time ``=`` time.time()`\
`    `\
`    ``# ─── STAGE 1: INTAKE ───`\
`    ``# 1.1 Multilingual preprocessing`\
`    lang_result ``=`` multilingual_pipeline.process(request[``"query"``])`\
`    corrected_query ``=`` lang_result[``"corrected"``]`\
`    detected_language ``=`` lang_result[``"language"``]`\
`    `\
`    ``# 1.2 Intent classification`\
`    intent ``=`` classify_intent(corrected_query)`\
`    confidence ``=`` intent[``"confidence"``]`\
`    `\
`    ``# 1.3 Persona selection`\
`    persona ``=`` select_persona(intent, request.get(``"persona_hint"``))`\
`    `\
`    ``# 1.4 Context loading`\
`    context ``=`` ``await`` load_context(`\
`        user_id``=``request[``"user_id"``],`\
`        client_id``=``request.get(``"client_id"``),`\
`        conversation_id``=``request.get(``"conversation_id"``),`\
`        persona``=``persona`\
`    )`\
`    `\
`    ``# ─── STAGE 2: BRAIN (NAFS) ───`\
`    ``# 2.1 Knowledge layer routing`\
`    layers ``=`` route_knowledge_layers(corrected_query, intent)`\
`    `\
`    ``# 2.2 Query each layer`\
`    parametric_result ``=`` ``await`` query_parametric(corrected_query, context, persona) ``if`` KnowledgeLayer.PARAMETRIC ``in`` layers ``else`` ``None`\
`    dynamic_result ``=`` ``await`` query_dynamic_kg(corrected_query, context) ``if`` KnowledgeLayer.DYNAMIC ``in`` layers ``else`` ``None`\
`    static_result ``=`` ``await`` query_static_corpus(corrected_query) ``if`` KnowledgeLayer.STATIC ``in`` layers ``else`` ``None`\
`    `\
`    ``# 2.3 Fuse results`\
`    fused_response ``=`` fuse_knowledge(`\
`        parametric``=``parametric_result,`\
`        dynamic``=``dynamic_result,`\
`        static``=``static_result,`\
`        weights``=``NAFS_WEIGHTS`\
`    )`\
`    `\
`    ``# ─── STAGE 3: TOOLS (if needed) ───`\
`    tool_results ``=`` []`\
`    ``if`` intent[``"requires_tool"``]:`\
`        tools ``=`` select_tools(intent, corrected_query)`\
`        ``for`` tool ``in`` tools:`\
`            result ``=`` ``await`` execute_tool(tool, corrected_query, context)`\
`            tool_results.append(result)`\
`        `\
`        ``# Integrate tool results into response`\
`        fused_response ``=`` integrate_tool_results(fused_response, tool_results)`\
`    `\
`    ``# ─── STAGE 4: QUALITY (HAYAT) ───`\
`    ``# 4.1 Initial CQF scoring`\
`    cqf ``=`` score_cqf(fused_response, context)`\
`    `\
`    ``# 4.2 Iteration loop`\
`    iterations ``=`` ``0`\
`    current_response ``=`` fused_response`\
`    `\
`    ``while`` cqf[``"total"``] ``<`` CQF_TARGET ``and`` iterations ``<`` MAX_ITERATIONS:`\
`        ``# Analyze weaknesses`\
`        weaknesses ``=`` analyze_weaknesses(cqf)`\
`        `\
`        ``# Refine`\
`        refined_query ``=`` build_refinement_prompt(corrected_query, current_response, weaknesses)`\
`        `\
`        ``# Regenerate`\
`        current_response ``=`` ``await`` regenerate(refined_query, context, persona)`\
`        `\
`        ``# Re-score`\
`        cqf ``=`` score_cqf(current_response, context)`\
`        iterations ``+=`` ``1`\
`    `\
`    ``# ─── STAGE 5: SAFETY (MAQASHID) ───`\
`    maqashid_result ``=`` apply_maqashid_filter(`\
`        response``=``current_response,`\
`        mode``=``request.get(``"maqashid_mode"``, ``"GENERAL"``),`\
`        persona``=``persona`\
`    )`\
`    `\
`    ``if`` ``not`` maqashid_result[``"passed"``]:`\
`        ``return`` {`\
`            ``"success"``: ``False``,`\
`            ``"error"``: {`\
`                ``"code"``: ``"GEN003"``,`\
`                ``"message"``: maqashid_result[``"reason"``],`\
`                ``"details"``: maqashid_result[``"violations"``]`\
`            }`\
`        }`\
`    `\
`    ``# ─── STAGE 6: LABELING ───`\
`    epistemic_labels ``=`` label_epistemic(current_response, layers, tool_results)`\
`    sanad_chain ``=`` build_sanad_chain(layers, tool_results)`\
`    `\
`    ``# ─── STAGE 7: LEARNING (AQL) ───`\
`    ``await`` capture_for_learning(`\
`        query``=``corrected_query,`\
`        response``=``current_response,`\
`        cqf``=``cqf,`\
`        context``=``context,`\
`        layers``=``layers`\
`    )`\
`    `\
`    ``# ─── STAGE 8: HEALTH (QALB) ───`\
`    health ``=`` ``await`` check_health()`\
`    `\
`    ``# ─── STAGE 9: FORMAT ───`\
`    formatted ``=`` format_response(`\
`        content``=``current_response,`\
`        labels``=``epistemic_labels,`\
`        sanad``=``sanad_chain,`\
`        cqf``=``cqf,`\
`        persona``=``persona,`\
`        language``=``detected_language`\
`    )`\
`    `\
`    ``# ─── STAGE 10: DELIVER ───`\
`    duration_ms ``=`` ``int``((time.time() ``-`` start_time) ``*`` ``1000``)`\
`    `\
`    ``return`` {`\
`        ``"success"``: ``True``,`\
`        ``"data"``: {`\
`            ``"response"``: formatted,`\
`            ``"assets"``: extract_assets(tool_results),`\
`            ``"metadata"``: {`\
`                ``"language"``: detected_language,`\
`                ``"persona"``: persona,`\
`                ``"cqf_score"``: cqf[``"total"``],`\
`                ``"iterations"``: iterations,`\
`                ``"layers_used"``: [l.value ``for`` l ``in`` layers],`\
`                ``"epistemic_labels"``: epistemic_labels,`\
`                ``"sanad_chain"``: sanad_chain,`\
`                ``"health"``: health[``"status"``],`\
`                ``"duration_ms"``: duration_ms`\
`            }`\
`        },`\
`        ``"meta"``: {`\
`            ``"request_id"``: generate_request_id(),`\
`            ``"timestamp"``: datetime.utcnow().isoformat(),`\
`            ``"duration_ms"``: duration_ms`\
`        }`\
`    }`

### 1.2 Complexity Analysis

| Stage    | Time Complexity | Space Complexity | Bottleneck                      |
|:---------|:----------------|:-----------------|:--------------------------------|
| Intake   | O(n)            | O(1)             | Typo dictionary lookup          |
| Nafs     | O(m × k)        | O(k)             | LLM inference (m = model size)  |
| Tools    | O(t × p)        | O(p)             | Tool execution (t = tool count) |
| Hayat    | O(i × m × k)    | O(k)             | Iteration loop                  |
| Maqashid | O(n × r)        | O(1)             | Rule matching (r = rules)       |
| Total    | O(i × m × k)    | O(k + p)         | LLM inference                   |

------------------------------------------------------------------------

## 2. RAUDAH TASK DECOMPOSITION ALGORITHM

### 2.1 DAG Construction

`def`` decompose_to_dag(brief: ``str``, agents: ``list``) ``->`` TaskGraph:`\
`    ``"""`\
`    Decompose creative brief into directed acyclic graph.`\
`    """`\
`    ``# Step 1: Extract requirements from brief`\
`    requirements ``=`` extract_requirements(brief)`\
`    ``# Returns: {"research_needed": True, "visual_count": 5, "copy_count": 10, ...}`\
`    `\
`    ``# Step 2: Identify task types`\
`    tasks ``=`` []`\
`    `\
`    ``if`` requirements[``"research_needed"``]:`\
`        tasks.append(Task(`\
`            ``id``=``"research"``,`\
`            agent``=``"ABOO"``,`\
`            action``=``"market_research"``,`\
`            dependencies``=``[],`\
`            output_type``=``"research_report"`\
`        ))`\
`    `\
`    tasks.append(Task(`\
`        ``id``=``"concept"``,`\
`        agent``=``"AYMAN"``,`\
`        action``=``"generate_concept"``,`\
`        dependencies``=``[``"research"``] ``if`` requirements[``"research_needed"``] ``else`` [],`\
`        output_type``=``"creative_direction"`\
`    ))`\
`    `\
`    tasks.append(Task(`\
`        ``id``=``"visuals"``,`\
`        agent``=``"UTZ"``,`\
`        action``=``"generate_visuals"``,`\
`        dependencies``=``[``"concept"``],`\
`        output_type``=``"image_assets"``,`\
`        count``=``requirements[``"visual_count"``]`\
`    ))`\
`    `\
`    tasks.append(Task(`\
`        ``id``=``"copy"``,`\
`        agent``=``"ALEY"``,`\
`        action``=``"generate_copy"``,`\
`        dependencies``=``[``"concept"``],`\
`        output_type``=``"text_assets"``,`\
`        count``=``requirements[``"copy_count"``]`\
`    ))`\
`    `\
`    tasks.append(Task(`\
`        ``id``=``"production"``,`\
`        agent``=``"OOMAR"``,`\
`        action``=``"assemble_deliverables"``,`\
`        dependencies``=``[``"visuals"``, ``"copy"``],`\
`        output_type``=``"campaign_package"`\
`    ))`\
`    `\
`    ``# Step 3: Build graph`\
`    graph ``=`` TaskGraph()`\
`    ``for`` task ``in`` tasks:`\
`        graph.add_node(task)`\
`    `\
`    ``for`` task ``in`` tasks:`\
`        ``for`` dep_id ``in`` task.dependencies:`\
`            graph.add_edge(dep_id, task.``id``)`\
`    `\
`    ``# Step 4: Validate (no cycles)`\
`    ``if`` ``not`` graph.is_dag():`\
`        ``raise`` ``ValueError``(``"Task graph has cycles — invalid decomposition"``)`\
`    `\
`    ``return`` graph`

### 2.2 Parallel Execution

`async`` ``def`` execute_dag(graph: TaskGraph) ``->`` ``dict``:`\
`    ``"""`\
`    Execute DAG with maximum parallelism.`\
`    """`\
`    results ``=`` {}`\
`    in_progress ``=`` ``set``()`\
`    completed ``=`` ``set``()`\
`    `\
`    ``while`` ``len``(completed) ``<`` ``len``(graph.nodes):`\
`        ``# Find ready tasks (all dependencies completed)`\
`        ready ``=`` [`\
`            node ``for`` node ``in`` graph.nodes`\
`            ``if`` node.``id`` ``not`` ``in`` completed`\
`            ``and`` node.``id`` ``not`` ``in`` in_progress`\
`            ``and`` ``all``(dep ``in`` completed ``for`` dep ``in`` node.dependencies)`\
`        ]`\
`        `\
`        ``if`` ``not`` ready ``and`` in_progress:`\
`            ``# Wait for any in-progress task`\
`            done, _ ``=`` ``await`` asyncio.wait(`\
`                [task.future ``for`` task ``in`` in_progress],`\
`                return_when``=``asyncio.FIRST_COMPLETED`\
`            )`\
`            ``for`` task ``in`` done:`\
`                results[task.``id``] ``=`` task.result()`\
`                completed.add(task.``id``)`\
`                in_progress.remove(task)`\
`            ``continue`\
`        `\
`        ``# Launch all ready tasks in parallel`\
`        ``for`` task ``in`` ready:`\
`            task.future ``=`` asyncio.create_task(execute_task(task))`\
`            in_progress.add(task)`\
`    `\
`    ``# Wait for remaining tasks`\
`    ``if`` in_progress:`\
`        done, _ ``=`` ``await`` asyncio.wait(`\
`            [task.future ``for`` task ``in`` in_progress]`\
`        )`\
`        ``for`` task ``in`` done:`\
`            results[task.``id``] ``=`` task.result()`\
`            completed.add(task.``id``)`\
`    `\
`    ``return`` results`

### 2.3 Consensus Algorithm

`def`` reach_consensus(outputs: ``list``, criteria: ``list``, agent_weights: ``dict``) ``->`` ``dict``:`\
`    ``"""`\
`    When multiple agents produce alternatives, reach consensus.`\
`    """`\
`    ``# Score each output`\
`    scored_outputs ``=`` []`\
`    ``for`` output ``in`` outputs:`\
`        scores ``=`` {}`\
`        ``for`` criterion ``in`` criteria:`\
`            scores[criterion] ``=`` score_criterion(output, criterion)`\
`        `\
`        ``# Weight by agent expertise`\
`        agent ``=`` output[``"agent"``]`\
`        weight ``=`` agent_weights.get(agent, ``1.0``)`\
`        `\
`        total_score ``=`` ``sum``(scores.values()) ``/`` ``len``(scores) ``*`` weight`\
`        scored_outputs.append({`\
`            ``"output"``: output,`\
`            ``"scores"``: scores,`\
`            ``"total"``: total_score`\
`        })`\
`    `\
`    ``# Sort by score`\
`    scored_outputs.sort(key``=``lambda`` x: x[``"total"``], reverse``=``True``)`\
`    `\
`    ``# If top score significantly better → select it`\
`    ``if`` ``len``(scored_outputs) ``==`` ``1``:`\
`        ``return`` scored_outputs[``0``][``"output"``]`\
`    `\
`    best ``=`` scored_outputs[``0``]`\
`    second ``=`` scored_outputs[``1``]`\
`    `\
`    ``if`` best[``"total"``] ``>`` second[``"total"``] ``*`` ``1.2``:  ``# 20% better`\
`        ``return`` best[``"output"``]`\
`    `\
`    ``# Otherwise → synthesize hybrid`\
`    ``return`` synthesize_hybrid(`\
`        best[``"output"``],`\
`        second[``"output"``],`\
`        criteria`\
`    )`

------------------------------------------------------------------------

## 3. JARIYAH LEARNING ALGORITHM

### 3.1 Real-Time Capture

`async`` ``def`` capture_interaction(query: ``str``, response: ``str``, feedback: ``str``, cqf: ``float``):`\
`    ``"""`\
`    Capture interaction for learning.`\
`    """`\
`    ``# 1. Anonymize`\
`    anonymized_query ``=`` remove_pii(query)`\
`    anonymized_response ``=`` remove_pii(response)`\
`    `\
`    ``# 2. Quality gate`\
`    ``if`` cqf ``<`` ``7.0``:`\
`        ``return``  ``# Don't learn from low-quality interactions`\
`    `\
`    ``# 3. Check for PII leakage`\
`    ``if`` contains_pii(anonymized_query) ``or`` contains_pii(anonymized_response):`\
`        ``return``  ``# Skip if PII detected`\
`    `\
`    ``# 4. Categorize`\
`    category ``=`` categorize_interaction(query)`\
`    language ``=`` detect_language(query)`\
`    `\
`    ``# 5. Extract knowledge nuggets`\
`    nuggets ``=`` extract_knowledge_nuggets(query, response)`\
`    `\
`    ``# 6. Store training pair`\
`    pair_id ``=`` ``await`` db.training_pairs.insert({`\
`        ``"instruction"``: anonymized_query,`\
`        ``"response"``: anonymized_response,`\
`        ``"category"``: category,`\
`        ``"language"``: language,`\
`        ``"cqf_score"``: cqf,`\
`        ``"status"``: ``"pending"``,`\
`        ``"source"``: ``"user_chat"``,`\
`        ``"created_at"``: datetime.utcnow()`\
`    })`\
`    `\
`    ``# 7. Update Knowledge Graph`\
`    ``for`` nugget ``in`` nuggets:`\
`        ``await`` kg.add_node(`\
`            label``=``"Concept"``,`\
`            name``=``nugget[``"subject"``],`\
`            properties``=``nugget[``"properties"``],`\
`            source``=``"user_interaction"``,`\
`            confidence``=``nugget[``"confidence"``]`\
`        )`\
`    `\
`    ``# 8. Check drift`\
`    ``await`` check_drift_trigger()`

### 3.2 Drift Detection

`async`` ``def`` check_drift() ``->`` ``dict``:`\
`    ``"""`\
`    Detect if model performance has drifted.`\
`    """`\
`    ``# Get last week's interactions`\
`    last_week ``=`` ``await`` get_interactions(days``=``7``)`\
`    previous_week ``=`` ``await`` get_interactions(days``=``7``, offset``=``7``)`\
`    `\
`    ``# Calculate metrics`\
`    metrics ``=`` {`\
`        ``"avg_cqf"``: mean([i[``"cqf"``] ``for`` i ``in`` last_week]),`\
`        ``"prev_avg_cqf"``: mean([i[``"cqf"``] ``for`` i ``in`` previous_week]),`\
`        ``"thumbs_up_ratio"``: count_thumbs_up(last_week) ``/`` ``len``(last_week),`\
`        ``"prev_thumbs_ratio"``: count_thumbs_up(previous_week) ``/`` ``len``(previous_week),`\
`        ``"avg_response_time"``: mean([i[``"duration_ms"``] ``for`` i ``in`` last_week]),`\
`        ``"error_rate"``: count_errors(last_week) ``/`` ``len``(last_week)`\
`    }`\
`    `\
`    ``# Check thresholds`\
`    drift_detected ``=`` ``False`\
`    reasons ``=`` []`\
`    `\
`    ``if`` metrics[``"avg_cqf"``] ``<`` metrics[``"prev_avg_cqf"``] ``*`` ``0.95``:`\
`        drift_detected ``=`` ``True`\
`        reasons.append(``f"CQF dropped ``{``metrics[``'prev_avg_cqf'``] ``-`` metrics[``'avg_cqf'``]``:.1f}``"``)`\
`    `\
`    ``if`` metrics[``"thumbs_up_ratio"``] ``<`` metrics[``"prev_thumbs_ratio"``] ``*`` ``0.90``:`\
`        drift_detected ``=`` ``True`\
`        reasons.append(``f"Satisfaction dropped ``{``(``1`` ``-`` metrics[``'thumbs_up_ratio'``]``/``metrics[``'prev_thumbs_ratio'``])``*``100``:.0f}``%"``)`\
`    `\
`    ``if`` metrics[``"error_rate"``] ``>`` ``0.05``:`\
`        drift_detected ``=`` ``True`\
`        reasons.append(``f"Error rate at ``{``metrics[``'error_rate'``]``*``100``:.1f}``%"``)`\
`    `\
`    ``return`` {`\
`        ``"drift_detected"``: drift_detected,`\
`        ``"severity"``: ``"high"`` ``if`` ``len``(reasons) ``>=`` ``2`` ``else`` ``"medium"`` ``if`` drift_detected ``else`` ``"none"``,`\
`        ``"metrics"``: metrics,`\
`        ``"reasons"``: reasons,`\
`        ``"recommendation"``: ``"retrain"`` ``if`` drift_detected ``else`` ``"monitor"`\
`    }`

------------------------------------------------------------------------

## 4. CQF (CONTENT QUALITY FRAMEWORK) ALGORITHM

### 4.1 Scoring Algorithm

`def`` score_cqf(output: ``str``, context: ``dict``) ``->`` ``dict``:`\
`    ``"""`\
`    Score output quality across 10 criteria.`\
`    """`\
`    criteria ``=`` {`\
`        ``"accuracy"``: {`\
`            ``"weight"``: ``0.20``,`\
`            ``"score"``: score_accuracy(output, context[``"sources"``])`\
`        },`\
`        ``"relevance"``: {`\
`            ``"weight"``: ``0.15``,`\
`            ``"score"``: score_relevance(output, context[``"query"``])`\
`        },`\
`        ``"completeness"``: {`\
`            ``"weight"``: ``0.15``,`\
`            ``"score"``: score_completeness(output, context[``"query"``])`\
`        },`\
`        ``"clarity"``: {`\
`            ``"weight"``: ``0.10``,`\
`            ``"score"``: score_clarity(output)`\
`        },`\
`        ``"epistemic_honesty"``: {`\
`            ``"weight"``: ``0.10``,`\
`            ``"score"``: score_epistemic_honesty(output)`\
`        },`\
`        ``"cultural"``: {`\
`            ``"weight"``: ``0.10``,`\
`            ``"score"``: score_cultural_appropriateness(output, context[``"language"``])`\
`        },`\
`        ``"source_citation"``: {`\
`            ``"weight"``: ``0.05``,`\
`            ``"score"``: score_source_citation(output, context[``"sources"``])`\
`        },`\
`        ``"actionability"``: {`\
`            ``"weight"``: ``0.05``,`\
`            ``"score"``: score_actionability(output)`\
`        },`\
`        ``"creativity"``: {`\
`            ``"weight"``: ``0.05``,`\
`            ``"score"``: score_creativity(output)`\
`        },`\
`        ``"safety"``: {`\
`            ``"weight"``: ``0.05``,`\
`            ``"score"``: score_safety(output)`\
`        }`\
`    }`\
`    `\
`    ``# Calculate weighted total`\
`    total ``=`` ``sum``(`\
`        c[``"score"``] ``*`` c[``"weight"``] `\
`        ``for`` c ``in`` criteria.values()`\
`    ) ``*`` ``10``  ``# Scale to 0-10`\
`    `\
`    ``return`` {`\
`        ``"total"``: ``round``(total, ``1``),`\
`        ``"criteria"``: {k: ``round``(v[``"score"``] ``*`` ``10``, ``1``) ``for`` k, v ``in`` criteria.items()},`\
`        ``"pass"``: total ``>=`` ``7.0``,`\
`        ``"excellent"``: total ``>=`` ``8.0``,`\
`        ``"weaknesses"``: [`\
`            k ``for`` k, v ``in`` criteria.items() `\
`            ``if`` v[``"score"``] ``*`` ``10`` ``<`` ``6.0`\
`        ]`\
`    }`

### 4.2 Individual Scorers

`def`` score_accuracy(output: ``str``, sources: ``list``) ``->`` ``float``:`\
`    ``"""`\
`    Check if output matches verified sources.`\
`    """`\
`    ``if`` ``not`` sources:`\
`        ``return`` ``0.5``  ``# No sources = uncertain`\
`    `\
`    verified ``=`` ``sum``(``1`` ``for`` s ``in`` sources ``if`` s.tier ``<=`` ``2``)`\
`    total ``=`` ``len``(sources)`\
`    `\
`    ``return`` verified ``/`` total ``if`` total ``>`` ``0`` ``else`` ``0.5`\
\
`def`` score_relevance(output: ``str``, query: ``str``) ``->`` ``float``:`\
`    ``"""`\
`    Semantic similarity between output and query intent.`\
`    """`\
`    ``# Use embedding similarity`\
`    output_embedding ``=`` embed(output)`\
`    query_embedding ``=`` embed(query)`\
`    `\
`    similarity ``=`` cosine_similarity(output_embedding, query_embedding)`\
`    `\
`    ``# Boost if query keywords appear in output`\
`    query_keywords ``=`` extract_keywords(query)`\
`    keyword_coverage ``=`` ``sum``(``1`` ``for`` kw ``in`` query_keywords ``if`` kw ``in`` output.lower()) ``/`` ``len``(query_keywords)`\
`    `\
`    ``return`` ``0.7`` ``*`` similarity ``+`` ``0.3`` ``*`` keyword_coverage`\
\
`def`` score_cultural_appropriateness(output: ``str``, language: ``str``) ``->`` ``float``:`\
`    ``"""`\
`    Check if output respects cultural norms.`\
`    """`\
`    ``# Check for inappropriate content`\
`    inappropriate_markers ``=`` load_cultural_markers(language)`\
`    violations ``=`` ``sum``(``1`` ``for`` marker ``in`` inappropriate_markers ``if`` marker ``in`` output.lower())`\
`    `\
`    ``if`` violations ``>`` ``0``:`\
`        ``return`` ``max``(``0.0``, ``1.0`` ``-`` violations ``*`` ``0.3``)`\
`    `\
`    ``# Check for positive cultural references`\
`    positive_markers ``=`` load_positive_cultural_markers(language)`\
`    positives ``=`` ``sum``(``1`` ``for`` marker ``in`` positive_markers ``if`` marker ``in`` output.lower())`\
`    `\
`    base ``=`` ``0.8`\
`    bonus ``=`` ``min``(``0.2``, positives ``*`` ``0.05``)`\
`    `\
`    ``return`` base ``+`` bonus`

------------------------------------------------------------------------

## 5. NAFS KNOWLEDGE FUSION ALGORITHM

### 5.1 Weighted Fusion

`def`` fuse_knowledge(parametric, dynamic, static, weights) ``->`` ``str``:`\
`    ``"""`\
`    Fuse responses from 3 knowledge layers.`\
`    """`\
`    responses ``=`` []`\
`    `\
`    ``if`` parametric:`\
`        responses.append({`\
`            ``"text"``: parametric,`\
`            ``"weight"``: weights[KnowledgeLayer.PARAMETRIC],`\
`            ``"source"``: ``"LLM"`\
`        })`\
`    `\
`    ``if`` dynamic:`\
`        responses.append({`\
`            ``"text"``: dynamic,`\
`            ``"weight"``: weights[KnowledgeLayer.DYNAMIC],`\
`            ``"source"``: ``"KG"`\
`        })`\
`    `\
`    ``if`` static:`\
`        responses.append({`\
`            ``"text"``: static,`\
`            ``"weight"``: weights[KnowledgeLayer.STATIC],`\
`            ``"source"``: ``"Corpus"`\
`        })`\
`    `\
`    ``if`` ``len``(responses) ``==`` ``1``:`\
`        ``return`` responses[``0``][``"text"``]`\
`    `\
`    ``if`` ``len``(responses) ``==`` ``2``:`\
`        ``# Weighted blend of two`\
`        ``return`` blend_two(responses[``0``], responses[``1``])`\
`    `\
`    ``# All three — use LLM to synthesize`\
`    synthesis_prompt ``=`` ``f"""`\
`    Synthesize these perspectives into one coherent response:`\
`    `\
`    [Parametric knowledge - weight ``{``weights[KnowledgeLayer.PARAMETRIC]``}``]:`\
`    ``{``parametric``}`\
`    `\
`    [Dynamic knowledge - weight ``{``weights[KnowledgeLayer.DYNAMIC]``}``]:`\
`    ``{``dynamic``}`\
`    `\
`    [Static knowledge - weight ``{``weights[KnowledgeLayer.STATIC]``}``]:`\
`    ``{``static``}`\
`    `\
`    Instructions:`\
`    - Prioritize factual accuracy`\
`    - Include source attributions where relevant`\
`    - Resolve any contradictions by favoring the higher-weighted source`\
`    - Maintain the user's query language`\
`    """`\
`    `\
`    ``return`` query_llm(synthesis_prompt)`

### 5.2 Topic Routing

`TOPIC_ROUTING ``=`` {`\
`    ``# General knowledge → Parametric only`\
`    ``"umum"``: [KnowledgeLayer.PARAMETRIC],`\
`    ``"teknologi"``: [KnowledgeLayer.PARAMETRIC],`\
`    ``"science"``: [KnowledgeLayer.PARAMETRIC],`\
`    ``"news"``: [KnowledgeLayer.PARAMETRIC, KnowledgeLayer.DYNAMIC],`\
`    `\
`    ``# SIDIX-specific → Dynamic + Static`\
`    ``"ihos"``: [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],`\
`    ``"maqashid"``: [KnowledgeLayer.DYNAMIC, KnowledgeLayer.STATIC],`\
`    ``"sidix_system"``: [KnowledgeLayer.DYNAMIC],`\
`    `\
`    ``# Religious/Ethical → Static first`\
`    ``"agama"``: [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],`\
`    ``"etika"``: [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],`\
`    ``"hukum"``: [KnowledgeLayer.STATIC, KnowledgeLayer.DYNAMIC],`\
`    `\
`    ``# Creative → Parametric + Dynamic`\
`    ``"creative"``: [KnowledgeLayer.PARAMETRIC, KnowledgeLayer.DYNAMIC],`\
`    ``"design"``: [KnowledgeLayer.PARAMETRIC, KnowledgeLayer.DYNAMIC],`\
`    ``"marketing"``: [KnowledgeLayer.PARAMETRIC, KnowledgeLayer.DYNAMIC],`\
`}`\
\
`def`` route_knowledge_layers(query: ``str``, intent: ``dict``) ``->`` ``list``:`\
`    ``"""`\
`    Determine which knowledge layers to query.`\
`    """`\
`    ``# Extract topic from query`\
`    topic ``=`` extract_topic(query)`\
`    `\
`    ``# Get routing for topic`\
`    layers ``=`` TOPIC_ROUTING.get(topic, [KnowledgeLayer.PARAMETRIC])`\
`    `\
`    ``# Adjust based on intent`\
`    ``if`` intent[``"type"``] ``==`` ``"religious_question"``:`\
`        ``# Prioritize static for religious topics`\
`        layers ``=`` [KnowledgeLayer.STATIC] ``+`` [l ``for`` l ``in`` layers ``if`` l ``!=`` KnowledgeLayer.STATIC]`\
`    `\
`    ``if`` intent[``"type"``] ``==`` ``"sidix_system"``:`\
`        ``# Always include dynamic for SIDIX-specific`\
`        ``if`` KnowledgeLayer.DYNAMIC ``not`` ``in`` layers:`\
`            layers.append(KnowledgeLayer.DYNAMIC)`\
`    `\
`    ``return`` layers`

------------------------------------------------------------------------

## 6. SANAD CHAIN ALGORITHM

### 6.1 Chain Construction

`def`` build_sanad_chain(layers: ``list``, tool_results: ``list``) ``->`` ``list``:`\
`    ``"""`\
`    Build provenance chain for output.`\
`    """`\
`    chain ``=`` []`\
`    `\
`    ``for`` layer ``in`` layers:`\
`        ``if`` layer ``==`` KnowledgeLayer.PARAMETRIC:`\
`            chain.append({`\
`                ``"source"``: ``"Qwen2.5-7B-Instruct"``,`\
`                ``"type"``: ``"model_weights"``,`\
`                ``"tier"``: ``3``,`\
`                ``"confidence"``: ``0.75``,`\
`                ``"verify_url"``: ``None`\
`            })`\
`        `\
`        ``elif`` layer ``==`` KnowledgeLayer.DYNAMIC:`\
`            ``# Get sources from Knowledge Graph`\
`            kg_sources ``=`` get_kg_sources(query)`\
`            ``for`` source ``in`` kg_sources:`\
`                chain.append({`\
`                    ``"source"``: source[``"name"``],`\
`                    ``"type"``: ``"knowledge_graph"``,`\
`                    ``"tier"``: source.get(``"tier"``, ``3``),`\
`                    ``"confidence"``: source.get(``"confidence"``, ``0.7``),`\
`                    ``"verify_url"``: source.get(``"url"``)`\
`                })`\
`        `\
`        ``elif`` layer ``==`` KnowledgeLayer.STATIC:`\
`            chain.append({`\
`                ``"source"``: ``"SIDIX Corpus"``,`\
`                ``"type"``: ``"curated_corpus"``,`\
`                ``"tier"``: ``2``,`\
`                ``"confidence"``: ``0.85``,`\
`                ``"verify_url"``: ``None`\
`            })`\
`    `\
`    ``# Add tool sources`\
`    ``for`` tool ``in`` tool_results:`\
`        chain.append({`\
`            ``"source"``: tool[``"name"``],`\
`            ``"type"``: ``"tool_execution"``,`\
`            ``"tier"``: ``2`` ``if`` tool[``"success"``] ``else`` ``4``,`\
`            ``"confidence"``: ``0.9`` ``if`` tool[``"success"``] ``else`` ``0.3``,`\
`            ``"verify_url"``: tool.get(``"source_url"``)`\
`        })`\
`    `\
`    ``# Sort by tier (most reliable first)`\
`    chain.sort(key``=``lambda`` x: x[``"tier"``])`\
`    `\
`    ``return`` chain`

------------------------------------------------------------------------

## 7. NASKH CONFLICT RESOLUTION ALGORITHM

### 7.1 Conflict Detection

`def`` detect_conflict(sources: ``list``) ``->`` ``dict``:`\
`    ``"""`\
`    Detect if sources contradict each other.`\
`    """`\
`    conflicts ``=`` []`\
`    `\
`    ``for`` i, source_a ``in`` ``enumerate``(sources):`\
`        ``for`` source_b ``in`` sources[i``+``1``:]:`\
`            ``# Check if same topic but different answers`\
`            ``if`` same_topic(source_a, source_b) ``and`` different_answer(source_a, source_b):`\
`                conflicts.append({`\
`                    ``"source_a"``: source_a,`\
`                    ``"source_b"``: source_b,`\
`                    ``"severity"``: calculate_conflict_severity(source_a, source_b)`\
`                })`\
`    `\
`    ``return`` {`\
`        ``"has_conflict"``: ``len``(conflicts) ``>`` ``0``,`\
`        ``"conflicts"``: conflicts,`\
`        ``"resolution_strategy"``: determine_resolution_strategy(conflicts)`\
`    }`

### 7.2 Resolution Strategy

`def`` resolve_conflict(source_a: ``dict``, source_b: ``dict``) ``->`` ``dict``:`\
`    ``"""`\
`    Resolve conflict between two sources.`\
`    """`\
`    tier_a ``=`` source_a[``"tier"``]`\
`    tier_b ``=`` source_b[``"tier"``]`\
`    `\
`    ``# Rule 1: Lower tier wins (1 is best)`\
`    ``if`` tier_a ``<`` tier_b:`\
`        ``return`` {``"winner"``: source_a, ``"reason"``: ``f"Higher tier (``{``tier_a``}`` < ``{``tier_b``}``)"``}`\
`    ``if`` tier_b ``<`` tier_a:`\
`        ``return`` {``"winner"``: source_b, ``"reason"``: ``f"Higher tier (``{``tier_b``}`` < ``{``tier_a``}``)"``}`\
`    `\
`    ``# Rule 2: Same tier — check recency`\
`    date_a ``=`` source_a.get(``"date"``, datetime.``min``)`\
`    date_b ``=`` source_b.get(``"date"``, datetime.``min``)`\
`    `\
`    ``if`` date_a ``>`` date_b:`\
`        ``return`` {``"winner"``: source_a, ``"reason"``: ``"More recent"``}`\
`    ``if`` date_b ``>`` date_a:`\
`        ``return`` {``"winner"``: source_b, ``"reason"``: ``"More recent"``}`\
`    `\
`    ``# Rule 3: Same tier, same date — present both`\
`    ``return`` {`\
`        ``"winner"``: ``None``,`\
`        ``"reason"``: ``"Same tier and date — present both sides"``,`\
`        ``"present_both"``: [source_a, source_b]`\
`    }`

------------------------------------------------------------------------

## 8. MULTILINGUAL DETECTION ALGORITHM

### 8.1 Language Detection

`def`` detect_language(text: ``str``) ``->`` ``dict``:`\
`    ``"""`\
`    Detect language from text.`\
`    Returns confidence scores for each language.`\
`    """`\
`    text_lower ``=`` text.lower()`\
`    scores ``=`` {}`\
`    `\
`    ``for`` lang_code, lang_data ``in`` LANGUAGE_MARKERS.items():`\
`        score ``=`` ``0.0`\
`        `\
`        ``# Word matching`\
`        words_found ``=`` ``sum``(``1`` ``for`` word ``in`` lang_data[``"words"``] ``if`` word ``in`` text_lower)`\
`        score ``+=`` ``min``(``1.0``, words_found ``/`` ``max``(``len``(lang_data[``"words"``]) ``*`` ``0.1``, ``5``))`\
`        `\
`        ``# Pattern matching`\
`        pattern_hits ``=`` ``sum``(``1`` ``for`` pattern ``in`` lang_data.get(``"patterns"``, []) `\
`                          ``if`` re.search(pattern, text_lower))`\
`        score ``+=`` ``min``(``1.0``, pattern_hits ``/`` ``max``(``len``(lang_data.get(``"patterns"``, [])), ``1``)) ``*`` ``0.5`\
`        `\
`        ``# Weight`\
`        score ``*=`` lang_data.get(``"weight"``, ``1.0``)`\
`        `\
`        scores[lang_code] ``=`` score`\
`    `\
`    ``# Sort and return`\
`    sorted_scores ``=`` ``sorted``(scores.items(), key``=``lambda`` x: x[``1``], reverse``=``True``)`\
`    primary ``=`` sorted_scores[``0``][``0``]`\
`    `\
`    ``# Check if mixed`\
`    is_mixed ``=`` ``len``(sorted_scores) ``>`` ``1`` ``and`` sorted_scores[``1``][``1``] ``>`` sorted_scores[``0``][``1``] ``*`` ``0.5`\
`    `\
`    ``return`` {`\
`        ``"primary"``: primary,`\
`        ``"scores"``: ``dict``(sorted_scores),`\
`        ``"is_mixed"``: is_mixed,`\
`        ``"confidence"``: ``min``(``1.0``, sorted_scores[``0``][``1``])`\
`    }`

------------------------------------------------------------------------

## 9. EPISTEMIC LABELING ALGORITHM

### 9.1 Auto-Labeling

`def`` auto_label(text: ``str``, sources: ``list``) ``->`` ``list``:`\
`    ``"""`\
`    Automatically apply epistemic labels to text.`\
`    """`\
`    labels ``=`` []`\
`    sentences ``=`` split_into_sentences(text)`\
`    `\
`    ``for`` sentence ``in`` sentences:`\
`        sentence_labels ``=`` []`\
`        `\
`        ``# Check for AI generation markers`\
`        ``if`` contains_generation_marker(sentence):`\
`            sentence_labels.append(``"CREATED"``)`\
`            ``continue``  ``# AI-generated content gets only CREATED`\
`        `\
`        ``# Check for factual claims`\
`        ``if`` is_factual_claim(sentence):`\
`            ``if`` has_verified_sources(sentence, sources):`\
`                sentence_labels.append(``"FACT"``)`\
`            ``else``:`\
`                sentence_labels.append(``"CLAIM"``)`\
`        `\
`        ``# Check for opinions`\
`        ``if`` contains_opinion_marker(sentence):`\
`            sentence_labels.append(``"OPINION"``)`\
`        `\
`        ``# Check for uncertainty`\
`        ``if`` contains_uncertainty_marker(sentence):`\
`            sentence_labels.append(``"UNKNOWN"``)`\
`        `\
`        ``# Check for references`\
`        ``if`` contains_reference_marker(sentence):`\
`            sentence_labels.append(``"REFERENCED"``)`\
`        `\
`        ``# Check for data-driven`\
`        ``if`` contains_data_marker(sentence):`\
`            sentence_labels.append(``"DATA-DRIVEN"``)`\
`        `\
`        ``if`` sentence_labels:`\
`            labels.append({`\
`                ``"sentence"``: sentence,`\
`                ``"labels"``: sentence_labels`\
`            })`\
`    `\
`    ``return`` labels`

------------------------------------------------------------------------

*Algorithms are the DNA of SIDIX. They must be correct, efficient, and
aligned with IHOS principles.*
