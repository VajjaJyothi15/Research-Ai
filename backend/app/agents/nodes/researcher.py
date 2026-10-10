from urllib.parse import urlparse
from app.agents.state import AgentState
from app.core.logging import logger
from app.tools.dispatcher import dispatcher


async def search_and_retrieval_node(state: AgentState, db=None) -> AgentState:
    mode = (state.mode or "standard").lower()
    norm_mode = "quick" if mode == "quick" else ("indepth" if mode in ["indepth", "deep", "academic"] else "standard")
    logger.info(f"Running Search & Retrieval Node for run_id: {state.run_id} (Mode: {norm_mode})")
    state.current_stage = "searching"
    state.status = "SEARCHING"

    if not state.plan or not state.plan.subquestions:
        state.logs.append("No subquestions found in plan to search.")
        return state

    existing_urls = {s.get("url") for s in state.sources if s.get("url")}

    # Configure query limits per subquestion based on mode
    if norm_mode == "quick":
        queries_limit = 1
        results_per_web = 2
        acad_results_limit = 1
    elif norm_mode == "indepth":
        queries_limit = 3
        results_per_web = 4
        acad_results_limit = 3
    else:  # standard
        queries_limit = 2
        results_per_web = 3
        acad_results_limit = 2

    for sq in state.plan.subquestions:
        if sq.status == "RESOLVED":
            continue

        # Check budget limit
        exceeded, reason = state.budget_tracker.is_exceeded(state.budget)
        if exceeded:
            state.logs.append(f"Search halted due to budget limit: {reason}")
            break

        for query in sq.search_queries[:queries_limit]:
            if len(state.sources) >= state.budget.max_sources:
                break

            state.logs.append(f"Executing web_search tool for query: '{query}'")
            try:
                # Dispatch web_search tool call
                search_results = await dispatcher.dispatch(
                    tool_name="web_search",
                    arguments={"query": query, "max_results": results_per_web},
                    run_id=state.run_id,
                    stage="searching",
                    db=db,
                )
                state.budget_tracker.tool_calls_used += 1

                for item in search_results:
                    url = item.url
                    if not url or url in existing_urls:
                        continue
                    
                    existing_urls.add(url)
                    extracted_content = item.snippet

                    # Try fetching full text via fetch_url tool if budget allows
                    if norm_mode != "quick":
                        try:
                            fetch_res = await dispatcher.dispatch(
                                tool_name="fetch_url",
                                arguments={"url": url},
                                run_id=state.run_id,
                                stage="extracting",
                                db=db,
                            )
                            state.budget_tracker.tool_calls_used += 1
                            if fetch_res.extracted_text and len(fetch_res.extracted_text.strip()) > 50:
                                extracted_content = fetch_res.extracted_text
                                if fetch_res.title and fetch_res.title != "Untitled":
                                    item.title = fetch_res.title
                        except Exception as fe:
                            logger.warning(f"Live page fetch failed for URL '{url}', using search snippet: {fe}")

                    state.budget_tracker.sources_fetched += 1
                    source_record = {
                        "url": url,
                        "canonical_url": url.split("?")[0],
                        "title": item.title or "Web Reference",
                        "author": item.domain or "Web Source",
                        "publication_date": item.published_date or "2026-01-01",
                        "source_type": item.source_type,
                        "domain": item.domain or urlparse(url).netloc or "web",
                        "relevance_score": 0.92,
                        "content_text": extracted_content,
                    }
                    state.sources.append(source_record)

            except Exception as se:
                logger.error(f"Search tool call failed for query '{query}': {se}")

        # Dispatch academic search if enabled
        if state.policy.allow_academic_papers and len(state.sources) < state.budget.max_sources:
            try:
                acad_results = await dispatcher.dispatch(
                    tool_name="search_academic_sources",
                    arguments={"query": sq.question, "max_results": acad_results_limit},
                    run_id=state.run_id,
                    stage="searching",
                    db=db,
                )
                state.budget_tracker.tool_calls_used += 1
                for paper in acad_results:
                    if not paper.url or paper.url in existing_urls:
                        continue
                    
                    existing_urls.add(paper.url)
                    state.budget_tracker.sources_fetched += 1
                    state.sources.append({
                        "url": paper.url,
                        "canonical_url": paper.url,
                        "title": paper.title,
                        "author": ", ".join(paper.authors) if paper.authors else "Academic Researcher",
                        "publication_date": str(paper.publication_year or "2025"),
                        "source_type": "academic",
                        "domain": urlparse(paper.url).netloc or "academic",
                        "relevance_score": 0.96,
                        "content_text": paper.abstract,
                    })
            except Exception as ae:
                logger.warning(f"Academic search failed for subquestion '{sq.question}': {ae}")

        sq.status = "RESOLVED"

    state.logs.append(f"Search & Retrieval completed ({norm_mode} mode). Total sources gathered: {len(state.sources)}")
    return state

