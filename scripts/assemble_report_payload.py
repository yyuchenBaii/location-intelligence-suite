import json
import sys
from pathlib import Path


def _load_json(path_str):
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def _point_from_contract(contract):
    location = contract.get("location") or {}
    point = location.get("point") or {}
    lng = point.get("lng")
    lat = point.get("lat")
    if lng in (None, "") or lat in (None, ""):
        raise ValueError("upstream contract must include location.point.lng and location.point.lat")
    return [float(lng), float(lat)]


def _context_from_contract(contract):
    location = contract.get("location") or {}
    mobility = contract.get("mobility") or {}
    supply = contract.get("supply") or {}
    metro = mobility.get("nearest_metro") or {}
    metro_capture = mobility.get("metro_capture") or {}
    anchor = mobility.get("nearest_commercial_anchor") or {}
    aoi = location.get("aoi") or {}

    return {
        "province": location.get("province", ""),
        "city": location.get("city", ""),
        "district": location.get("district", ""),
        "adcode": location.get("adcode", ""),
        "township": location.get("township", ""),
        "street_address": location.get("street_address", ""),
        "formatted_address": location.get("formatted_address", ""),
        "business_areas": location.get("business_areas") or [],
        "nearby_landmarks": location.get("nearby_landmarks") or [],
        "aoi_name": aoi.get("name", ""),
        "aoi_area_sqm": aoi.get("area_sqm", ""),
        "nearest_metro": metro.get("name", "") or "1500m内无地铁站",
        "nearest_metro_location": metro.get("location", ""),
        "metro_walk_minutes": metro.get("walk_minutes"),
        "metro_walk_meters": metro.get("walk_meters"),
        "metro_flow_capture": bool(metro_capture.get("captured")),
        "metro_flow_label": metro_capture.get("label", ""),
        "metro_access": mobility.get("metro_access") or {},
        "nearest_commercial_anchor": anchor.get("name", "") or "1500m内未识别大型商业锚点",
        "nearest_commercial_anchor_distance_m": anchor.get("distance_m"),
        "nearest_commercial_anchor_location": anchor.get("location", ""),
        "nearest_commercial_anchor_address": anchor.get("address", ""),
        "anchor_access": mobility.get("anchor_access") or {},
        "anchor_access_label": mobility.get("anchor_access_label", ""),
        "office_count": supply.get("office_count_500m", 0),
        "residential_count": supply.get("residential_count_500m", 0),
        "_note": contract.get("notes") or "数据已通过统一 upstream contract 注入。",
    }


def _poi_from_contract(contract):
    competition = contract.get("competition") or {}
    nearest = competition.get("nearest_competitor") or {}
    map_points = competition.get("map_points") or []
    top_threats = competition.get("top_threats") or []

    return {
        "search_keyword": competition.get("keyword", ""),
        "search_mode": competition.get("search_mode"),
        "search_radius_meters": competition.get("search_radius_meters"),
        "search_polygon": competition.get("search_polygon"),
        "search_city": competition.get("search_city"),
        "search_adcode": competition.get("search_adcode"),
        "total_competitors_found": competition.get("total_poi", 0),
        "fetched_sample_size": competition.get("fetched_sample_size", 0),
        "closest_competitor": {
            "id": nearest.get("id", ""),
            "name": nearest.get("name", ""),
            "distance_m": nearest.get("distance_m"),
            "rating": nearest.get("rating", "暂无"),
            "avg_cost_yuan": nearest.get("avg_cost_yuan", "暂无"),
            "business_area": nearest.get("business_area", ""),
            "location": nearest.get("location", ""),
            "detail": nearest.get("detail") or {},
        },
        "competition_level": competition.get("level_label"),
        "price_distribution": competition.get("price_distribution") or {},
        "price_insight": competition.get("price_insight"),
        "rating_avg": competition.get("rating_avg"),
        "high_quality_count": competition.get("high_quality_count", 0),
        "top_threats": top_threats,
        "top_threats_count": competition.get("top_threats_count", len(top_threats)),
        "business_areas_covered": competition.get("business_areas_covered") or [],
        "top_competitors_for_map": map_points,
    }


def _load_analysis_inputs(entry):
    if entry.get("upstream_contract_path"):
        contract = _load_json(entry["upstream_contract_path"])
        context = _context_from_contract(contract)
        poi = _poi_from_contract(contract)
        lnglat = _point_from_contract(contract)
        return context, poi, lnglat, contract

    context = _load_json(entry["context_path"])
    poi = _load_json(entry["poi_path"])
    lnglat = _parse_lnglat(entry["lnglat"])
    return context, poi, lnglat, None


def _parse_lnglat(value):
    if isinstance(value, list) and len(value) == 2:
        return [float(value[0]), float(value[1])]
    if isinstance(value, str) and "," in value:
        lng, lat = value.split(",", 1)
        return [float(lng), float(lat)]
    raise ValueError("lnglat must be a [lng, lat] list or 'lng,lat' string")


def _clamp(num, low=0, high=100):
    return max(low, min(high, int(round(num))))


def _grade_from_score(score):
    if score >= 85:
        return "A- 强势推荐", "safe"
    if score >= 70:
        return "B 可进场", "safe"
    if score >= 55:
        return "B- 谨慎评估", "warn"
    if score >= 40:
        return "C 高压竞争", "warn"
    return "D 不建议进场", "danger"


def _risk_color(grade_class):
    if grade_class == "safe":
        return "var(--success)"
    if grade_class == "warn":
        return "var(--warning)"
    return "var(--danger)"


def _safe_text(value, default="暂无"):
    return value if value not in (None, "", [], {}) else default


def _normalize_cost(value):
    if value in (None, "", "暂无"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _nearest_competitor_line(poi):
    comp = poi.get("closest_competitor") or {}
    name = _safe_text(comp.get("name"))
    dist = comp.get("distance_m")
    rating = _safe_text(comp.get("rating"))
    cost = _safe_text(comp.get("avg_cost_yuan"))
    return name, dist, rating, cost


def _price_band_summary(poi):
    dist = poi.get("price_distribution") or {}
    return (
        f"低价 {dist.get('cheap', 0)} 家 / "
        f"中档 {dist.get('moderate', 0)} 家 / "
        f"高价 {dist.get('expensive', 0)} 家 / "
        f"未标价 {dist.get('unknown', 0)} 家"
    )


def _top_threat_html(poi):
    threats = poi.get("top_threats") or []
    if not threats:
        return "500m 内未检出评分 ≥4.0 的高威胁竞品。"

    lines = []
    for item in threats[:5]:
        cost = item.get("avg_cost_yuan")
        cost_text = f"{cost:.0f} 元" if isinstance(cost, (int, float)) else "未标价"
        lines.append(
            f"• {item.get('name', '未命名竞品')} | {item.get('distance_m', '?')}m | "
            f"评分 {item.get('rating', '暂无')} | 客单 {cost_text}"
        )
    return "<br>".join(lines)


def _map_competitor_pois(poi):
    mapped = []
    for item in (poi.get("top_competitors_for_map") or [])[:30]:
        loc = item.get("location")
        if not loc:
            continue
        try:
            lnglat = _parse_lnglat(loc)
        except ValueError:
            continue
        rating = _safe_text(item.get("rating"))
        avg_cost = _safe_text(item.get("avg_cost"))
        distance = item.get("distance_m", "?")
        area = item.get("business_area") or "商圈未标注"
        mapped.append(
            {
                "loc": lnglat,
                "name": item.get("name", "未命名竞品"),
                "type": "competitor",
                "desc": f"距离 {distance}m | 评分 {rating} | 客单 {avg_cost} | {area}",
            }
        )
    return mapped


def _legend_items(include_office=False):
    items = [
        {"color": "var(--accent-cyan)", "label": "目标选址点"},
        {"color": "var(--danger)", "label": "竞品 / 风险点位"},
    ]
    if include_office:
        items.insert(1, {"color": "var(--success)", "label": "办公/客流锚点"})
    return items


def _transport_score(context):
    walk = context.get("metro_walk_minutes")
    if walk is None:
        return 35
    if walk <= 5:
        return 90
    if walk <= 10:
        return 75
    if walk <= 15:
        return 60
    return 45


def _traffic_score(context):
    office = int(context.get("office_count") or 0)
    residential = int(context.get("residential_count") or 0)
    mix = office * 1.2 + residential
    base = 35 + min(50, mix * 2.5)
    if context.get("metro_flow_capture"):
        base += 10
    return _clamp(base)


def _consumption_score(poi):
    price = poi.get("price_distribution") or {}
    expensive = int(price.get("expensive", 0))
    moderate = int(price.get("moderate", 0))
    rating_avg = poi.get("rating_avg") or 0
    return _clamp(35 + expensive * 3 + moderate * 1.5 + float(rating_avg) * 8)


def _competition_score(poi):
    total = int(poi.get("total_competitors_found") or 0)
    threats = int(poi.get("top_threats_count") or 0)
    return _clamp(95 - total * 1.1 - threats * 6)


def _cost_friendliness_score(poi):
    total = int(poi.get("total_competitors_found") or 0)
    return _clamp(75 - total * 0.8)


def _exposure_score(context, poi):
    landmarks = len(context.get("nearby_landmarks") or [])
    business_areas = len(context.get("business_areas") or [])
    metro_bonus = 10 if context.get("metro_flow_capture") else 0
    poi_bonus = min(20, len(poi.get("top_competitors_for_map") or []) // 2)
    return _clamp(45 + landmarks * 8 + business_areas * 10 + metro_bonus + poi_bonus)


def _radar_from_data(context, poi):
    return [
        {"item": "客流底盘", "score": _traffic_score(context)},
        {"item": "消费力", "score": _consumption_score(poi)},
        {"item": "交通可达性", "score": _transport_score(context)},
        {"item": "经营成本 (越低分表示成本越差)", "score": _cost_friendliness_score(poi)},
        {"item": "竞争蓝海度", "score": _competition_score(poi)},
        {"item": "品牌曝光价值", "score": _exposure_score(context, poi)},
    ]


def _summary_score(radar):
    weights = [0.22, 0.16, 0.14, 0.12, 0.24, 0.12]
    return _clamp(sum(item["score"] * weights[idx] for idx, item in enumerate(radar)))


def _business_area_label(context):
    areas = context.get("business_areas") or []
    if areas:
        return " / ".join(areas)
    return _safe_text(context.get("district"))


def _location_label(spec, context):
    if spec.get("location_label"):
        return spec["location_label"]
    district = context.get("district") or ""
    areas = context.get("business_areas") or []
    if district and areas:
        return f"{district}·{' / '.join(areas)}"
    return district or spec.get("location_name") or "待分析点位"


def _flow_conclusion(context):
    office = int(context.get("office_count") or 0)
    residential = int(context.get("residential_count") or 0)
    metro = context.get("metro_flow_label") or "无地铁结论"
    if office >= residential * 2 and office >= 6:
        pattern = "推断：办公潮汐主导，午高峰强于晚高峰。"
    elif residential >= office * 2 and residential >= 6:
        pattern = "推断：社区底盘更稳，晚间和周末承接能力更强。"
    else:
        pattern = "推断：办公与社区客流混合，全天分布更均衡。"
    return f"<strong>事实：</strong>{metro}<br><strong>推断：</strong>{pattern}"


def _traffic_analysis(context, poi):
    facts = []
    if context.get("formatted_address"):
        facts.append(f"落点地址：{context['formatted_address']}")
    if context.get("adcode"):
        facts.append(f"行政区编码：{context['adcode']}")
    if context.get("business_areas"):
        facts.append(f"所属商圈：{' / '.join(context['business_areas'])}")
    if context.get("aoi_name"):
        facts.append(f"所在 AOI：{context['aoi_name']}")
    if context.get("nearby_landmarks"):
        facts.append(f"周边地标：{'；'.join(context['nearby_landmarks'][:3])}")
    if poi.get("business_areas_covered"):
        facts.append(f"竞品覆盖商圈：{' / '.join(poi['business_areas_covered'][:4])}")
    if context.get("nearest_commercial_anchor") and context.get("nearest_commercial_anchor") != "1500m内未识别大型商业锚点":
        facts.append(
            f"最近商业锚点：{context['nearest_commercial_anchor']}，{context.get('anchor_access_label', '路径信息暂缺')}"
        )
    if poi.get("search_mode"):
        facts.append(f"竞品扫描方式：{poi['search_mode']}")
    facts_html = "<br>".join(f"• {line}" for line in facts) if facts else "• 暂无补充位置事实。"

    inference = []
    if context.get("metro_flow_capture"):
        inference.append("地铁步行可达，说明自然导入客流具备基础。")
    office = int(context.get("office_count") or 0)
    residential = int(context.get("residential_count") or 0)
    if office > residential:
        inference.append("办公底盘更强，工作日转化优先级高于周末。")
    elif residential > office:
        inference.append("社区底盘更厚，复购和晚间稳定性更值得期待。")
    else:
        inference.append("办公与居住底盘接近，经营时段不宜过于偏科。")
    return f"<strong>事实：</strong><br>{facts_html}<br><br><strong>推断：</strong>{' '.join(inference)}"


def _competition_progress(poi):
    total = int(poi.get("total_competitors_found") or 0)
    sample = max(1, int(poi.get("fetched_sample_size") or 1))
    threats = int(poi.get("top_threats_count") or 0)
    high_quality = int(poi.get("high_quality_count") or 0)
    return [
        {
            "label": f"2km 同品类总量 ({total}家)",
            "valueText": poi.get("competition_level") or "竞争强度待判定",
            "pct": _clamp(min(100, total * 2)),
            "colorClass": "bg-danger" if total > 40 else "bg-warn" if total > 20 else "bg-safe",
        },
        {
            "label": f"500m 高威胁竞品 ({threats}家)",
            "valueText": "近身竞争压力",
            "pct": _clamp(threats * 12),
            "colorClass": "bg-danger" if threats >= 5 else "bg-warn" if threats >= 2 else "bg-safe",
        },
        {
            "label": f"样本中高评分门店 ({high_quality}/{sample})",
            "valueText": "质量竞争强度",
            "pct": _clamp(high_quality / sample * 100),
            "colorClass": "bg-danger" if high_quality / sample >= 0.5 else "bg-warn" if high_quality / sample >= 0.25 else "bg-safe",
        },
    ]


def _competition_warning(poi):
    name, dist, rating, cost = _nearest_competitor_line(poi)
    header = f"<strong>最近竞品：</strong>{name}，距离 {dist if dist is not None else '?'}m，评分 {rating}，客单 {cost}"
    return f"{header}<br><br><strong>高威胁名单：</strong><br>{_top_threat_html(poi)}"


def _competition_risk(context, poi):
    total = int(poi.get("total_competitors_found") or 0)
    threats = int(poi.get("top_threats_count") or 0)
    metro_text = context.get("metro_flow_label") or "地铁可达性未知"
    risk = []
    if total >= 40:
        risk.append("同品类供给已经很厚，价格和展示面竞争会非常直接。")
    if threats >= 3:
        risk.append("500m 内高评分强威胁过多，新店需要明显差异化才有生存空间。")
    if not context.get("metro_flow_capture"):
        risk.append("地铁导流不足，意味着自然过客流更依赖街区本身。")
    if poi.get("search_mode") == "polygon":
        risk.append("本次竞争扫描基于明确边界，多数结果更接近真实商业体内部供给。")
    elif poi.get("search_mode") == "text":
        risk.append("本次竞争扫描基于城市范围检索，适合片区级对比，不应等同于门口即刻竞争。")
    if not risk:
        risk.append("当前未见极端竞争或交通短板，但仍需现场复核展示面与门头可见性。")
    return f"<strong>事实：</strong>{metro_text}<br><strong>推断：</strong>{' '.join(risk)}"


def _finance_block(spec, poi):
    rent_value = spec.get("rent_value") or "待补充租金"
    rent_sub = spec.get("rent_sub") or "当前脚本未接入租金数据"
    breakeven_value = spec.get("breakeven_value") or f"{max(40, int((poi.get('total_competitors_found') or 0) * 1.5 + 50))}+ 杯"
    breakeven_sub = spec.get("breakeven_sub") or "推断值，需结合租金复核"
    return {
        "rentLabel": spec.get("rent_label") or "租金数据状态",
        "rentValue": rent_value,
        "rentSub": rent_sub,
        "breakevenLabel": spec.get("breakeven_label") or "竞争保本压力",
        "breakevenValue": breakeven_value,
        "breakevenSub": breakeven_sub,
    }


def _roi_insight(spec, context, poi):
    if spec.get("roi_html"):
        return spec["roi_html"]
    total = int(poi.get("total_competitors_found") or 0)
    name, dist, rating, cost = _nearest_competitor_line(poi)
    return (
        f"<strong>事实：</strong>当前脚本没有真实租金，因此不能输出硬性的租售比结论。最近竞品为 {name}，"
        f"距离 {dist if dist is not None else '?'}m，评分 {rating}，客单 {cost}。<br>"
        f"<strong>推断：</strong>在 {total} 家同品类门店的竞争背景下，若租金超出同城常规水平，新店回本周期会被显著拉长。"
    )


def _revenue_insight(context, poi):
    return (
        f"<strong>事实：</strong>{poi.get('price_insight') or _price_band_summary(poi)}；样本均分 "
        f"{_safe_text(poi.get('rating_avg'))}；高评分门店 {poi.get('high_quality_count', 0)} 家。<br>"
        f"<strong>推断：</strong>营业上限更取决于你是否能避开最近强威胁并拿到足够清晰的差异化，而不是单纯依赖商圈热度。"
    )


def _compliance_insight(business_type):
    keyword = business_type or "该业态"
    heavy_food = any(word in keyword for word in ["火锅", "烧烤", "炒", "餐", "面", "麻辣烫", "烤"])
    if heavy_food:
        return "重餐饮优先核查独立排烟、380V 三相电、隔油池、消防改造条件以及夜间噪音投诉风险。"
    if "咖啡" in keyword or "茶" in keyword or "饮" in keyword:
        return "轻餐饮优先核查上下水、排水坡度、空调外机位、消防喷淋、外摆审批和招牌可视性。"
    return "优先核查消防、上下水、电力容量、招牌审批、物业营业时段限制和外摆政策。"


def _negotiation_insight(context, poi):
    name, dist, rating, cost = _nearest_competitor_line(poi)
    return (
        f"<strong>建议筹码：</strong><br>"
        f"1. 以 {name} 距点 {dist if dist is not None else '?'}m 的近身竞争作为压价依据。<br>"
        f"2. 以 {context.get('metro_flow_label') or '地铁导流有限'} 作为免租期和装修期谈判依据。<br>"
        f"3. 明确约束转让费、物业增项和招牌尺寸限制。"
    )


def _global_conclusion(location_name, business_type, score, grade, context, poi):
    nearest_name, dist, rating, cost = _nearest_competitor_line(poi)
    return (
        f"<strong>{location_name}</strong> 对 <strong>{business_type}</strong> 的综合判断为 <strong>{grade}</strong>（评分 {score}）。<br>"
        f"已确认事实：{context.get('metro_flow_label') or '地铁情况未知'}；"
        f"2km 内同类 {poi.get('total_competitors_found', 0)} 家；最近竞品 {nearest_name} 距 {dist if dist is not None else '?'}m，评分 {rating}，客单 {cost}。<br>"
        f"商业锚点：{context.get('nearest_commercial_anchor') or '暂无'}；{context.get('anchor_access_label') or '路径信息暂缺'}。<br>"
        f"推断建议：先把现场动线、门头可见性和真实租金谈清，再决定是否进入下一轮。"
    )


def _decision_reason(score, grade_class, context, poi):
    total = int(poi.get("total_competitors_found") or 0)
    threats = int(poi.get("top_threats_count") or 0)
    tone = "可进场，但必须控成本" if grade_class == "safe" else "可继续评估，但不能乐观" if grade_class == "warn" else "当前不建议进场"
    return (
        f"<strong>[决策理由]：</strong>{tone}。"
        f"高德事实显示同品类 {total} 家、近身高威胁 {threats} 家，"
        f"{context.get('metro_flow_label') or '地铁可达性待确认'}。"
        f" 最近商业锚点为 {context.get('nearest_commercial_anchor') or '暂无'}。"
        f"这说明机会来自结构性差异，而不是市场真空。"
    )


def _single_payload(spec):
    context, poi, lnglat, contract = _load_analysis_inputs(spec)
    if context.get("error"):
        raise ValueError(f"context error: {context['error']}")
    if poi.get("error"):
        raise ValueError(f"poi error: {poi['error']}")

    radar = _radar_from_data(context, poi)
    score = _summary_score(radar)
    grade, grade_class = _grade_from_score(score)
    color = _risk_color(grade_class)
    location_name = (
        spec.get("location_name")
        or ((contract or {}).get("location") or {}).get("label")
        or _location_label(spec, context)
    )
    business_type = (
        spec.get("business_type")
        or ((contract or {}).get("request") or {}).get("business_type")
        or poi.get("search_keyword")
        or "待分析业态"
    )

    nearest_name, dist, rating, cost = _nearest_competitor_line(poi)

    return {
        "header": {
            "title": spec.get("title") or "智能开店选址深度研报",
            "tag": spec.get("tag") or "AMap 实数分析",
            "dataSourceText": "数据源声明: 高德 LBS 实时查询 / 结构化推断",
            "locationLabel": _location_label(spec, context),
            "businessType": business_type,
            "statusText": spec.get("status_text") or "真实数据分析完成",
        },
        "intentHtml": (
            f"👤 <strong>分析对象：</strong>{location_name} 评估 <span class=\"hi\">{business_type}</span> 的落地可行性。"
            f" 当前重点读取 <span class=\"hi\">地铁可达性、办公/社区底盘、竞品密度、价格带</span> 四类高德事实。"
        ),
        "radar": radar,
        "metrics": {
            "trafficLabel": "最近竞品",
            "trafficValue": f"{nearest_name}",
            "trafficSub": f"距离 {dist if dist is not None else '?'}m | 评分 {rating} | 客单 {cost}",
            "conversionLabel": "价格带结构",
            "conversionValue": poi.get("competition_level") or "竞争待判定",
            "conversionSub": _price_band_summary(poi),
        },
        "flow": {
            "officeLabel": "周边 500m 写字楼/商务区",
            "officeCount": f"{context.get('office_count', 0)} 处",
            "residentialLabel": "周边 500m 住宅/小区",
            "residentialCount": f"{context.get('residential_count', 0)} 处",
        },
        "competition": {
            "progress": _competition_progress(poi),
        },
        "finance": _finance_block(spec, poi),
        "insights": {
            "trafficAnalysisHtml": _traffic_analysis(context, poi),
            "flowConclusionHtml": _flow_conclusion(context),
            "competitionWarningHtml": _competition_warning(poi),
            "competitionRiskHtml": _competition_risk(context, poi),
            "roiHtml": _roi_insight(spec, context, poi),
            "revenueHtml": _revenue_insight(context, poi),
            "complianceHtml": spec.get("compliance_html") or _compliance_insight(business_type),
            "negotiationHtml": spec.get("negotiation_html") or _negotiation_insight(context, poi),
            "globalConclusionHtml": spec.get("global_conclusion_html") or _global_conclusion(location_name, business_type, score, grade, context, poi),
            "decisionReasonHtml": spec.get("decision_reason_html") or _decision_reason(score, grade_class, context, poi),
        },
        "decision": {
            "score": str(score),
            "grade": grade,
            "gradeClass": grade_class,
        },
        "map": {
            "targetPoint": lnglat,
            "targetTitle": f"拟评估点位: {location_name}",
            "targetDescriptionHtml": (
                f"{context.get('formatted_address') or location_name}<br>"
                f"{context.get('metro_flow_label') or '地铁信息待确认'}"
            ),
            "circles": [
                {
                    "radius": 500,
                    "title": "近身竞争圈",
                    "desc": f"500m 内高威胁竞品 {poi.get('top_threats_count', 0)} 家。",
                    "color": "#ff1744" if int(poi.get("top_threats_count") or 0) >= 3 else "#ffea00",
                    "fillOpacity": 0.08,
                },
                {
                    "radius": 1000,
                    "title": "1km 观察圈",
                    "desc": f"同类总量 {poi.get('total_competitors_found', 0)} 家，竞争等级 {poi.get('competition_level') or '待判定'}。",
                    "color": color,
                    "fillOpacity": 0.05,
                },
            ],
            "pois": _map_competitor_pois(poi),
            "heatData": [],
            "legendItems": _legend_items(),
        },
    }


def _location_entry(entry, best_score):
    context, poi, lnglat, contract = _load_analysis_inputs(entry)
    if context.get("error"):
        raise ValueError(f"context error for {entry.get('id', '?')}: {context['error']}")
    if poi.get("error"):
        raise ValueError(f"poi error for {entry.get('id', '?')}: {poi['error']}")

    radar = _radar_from_data(context, poi)
    score = _summary_score(radar)
    grade, grade_class = _grade_from_score(score)
    business_type = (
        entry.get("business_type")
        or ((contract or {}).get("request") or {}).get("business_type")
        or poi.get("search_keyword")
        or "待分析业态"
    )
    nearest_name, dist, rating, cost = _nearest_competitor_line(poi)
    location_name = entry.get("name") or ((contract or {}).get("location") or {}).get("label") or "待分析点位"

    return {
        "computed_score": score,
        "payload": {
            "id": entry["id"],
            "name": location_name,
            "recommend": score == best_score,
            "latlng": lnglat,
            "score": score,
            "grade": grade,
            "gradeClass": grade_class,
            "color": _risk_color(grade_class),
            "radar": [
                {"item": "工作日客流", "score": radar[0]["score"]},
                {"item": "周末爆发客流", "score": _clamp((int(context.get("residential_count") or 0) * 8) + 35)},
                {"item": "客群隐形身价", "score": radar[1]["score"]},
                {"item": "经营成本友好度", "score": radar[3]["score"]},
                {"item": "竞争蓝海度", "score": radar[4]["score"]},
                {"item": "出片传播潜能", "score": radar[5]["score"]},
            ],
            "intent": (
                f"<strong>事实：</strong>{_location_label(entry, context)}，"
                f"{context.get('metro_flow_label') or '地铁情况未知'}。<br>"
                f"<strong>推断：</strong>该点位对 {business_type} 的可行性主要取决于"
                f"{'交通导流' if context.get('metro_flow_capture') else '街区自有客流'}与竞品差异化。"
            ),
            "metric1Label": "最近竞品",
            "metric1": nearest_name,
            "m1sub": f"{dist if dist is not None else '?'}m | 评分 {rating} | 客单 {cost}",
            "metric2Label": "竞品总量 / 高威胁",
            "metric2": f"{poi.get('total_competitors_found', 0)} / {poi.get('top_threats_count', 0)}",
            "m2sub": poi.get("competition_level") or "竞争待判定",
            "insight1": _traffic_analysis(context, poi),
            "progress": [
                {"label": row["label"], "pct": row["pct"], "color": row["colorClass"]}
                for row in _competition_progress(poi)
            ],
            "insight2": _competition_warning(poi),
            "finance1Label": "租金数据状态",
            "finance1": entry.get("rent_value") or "待补充租金",
            "finance2Label": "竞争保本压力",
            "finance2": entry.get("breakeven_value") or f"{max(40, int((poi.get('total_competitors_found') or 0) * 1.5 + 50))}+",
            "insight3": _roi_insight(entry, context, poi),
            "flowOffice": f"{context.get('office_count', 0)} 处",
            "flowResi": f"{context.get('residential_count', 0)} 处",
            "flowInsight": _flow_conclusion(context),
            "compInsight": _compliance_insight(business_type),
            "compNeg": _negotiation_insight(context, poi),
            "reason": _decision_reason(score, grade_class, context, poi),
            "circles": [
                {
                    "radius": 500,
                    "title": "近身竞争圈",
                    "desc": f"500m 内高威胁竞品 {poi.get('top_threats_count', 0)} 家。",
                    "color": "#ff1744" if int(poi.get("top_threats_count") or 0) >= 3 else "#ffea00",
                    "fillOpacity": 0.08,
                }
            ],
            "pois": _map_competitor_pois(poi),
            "heatData": [],
            "legendItems": _legend_items(),
        },
    }


def _compare_payload(spec):
    entries = spec.get("locations") or []
    if not entries:
        raise ValueError("compare spec requires locations")

    prelim = []
    best_score = -1
    for entry in entries:
        built = _location_entry(entry, -1)
        prelim.append(built)
        best_score = max(best_score, built["computed_score"])

    locations = {}
    ranking = []
    for idx, built in enumerate(prelim):
        payload = built["payload"]
        payload["recommend"] = payload["score"] == best_score
        locations[payload["id"]] = payload
        ranking.append((payload["score"], payload["name"], payload["grade"]))

    ranking.sort(reverse=True)
    ranking_html = "<br>".join(
        f"{index}. {name} | 评分 {score} | {grade}"
        for index, (score, name, grade) in enumerate(ranking, start=1)
    )

    return {
        "header": {
            "title": spec.get("title") or "多商圈深度对比研报",
            "tag": spec.get("tag") or "AMap 实数分析",
            "subtitle": spec.get("subtitle") or f"| {spec.get('business_type', '多点位对比')}",
            "dataSourceText": "数据源声明: 高德 LBS 实时查询 / 结构化推断",
        },
        "globalConclusionHtml": (
            f"<strong>综合排序：</strong><br>{ranking_html}<br><br>"
            f"<strong>最终建议：</strong>{ranking[0][1]} 当前综合得分最高，适合作为优先尽调对象。"
        ),
        "locations": locations,
    }


def main(argv):
    if len(argv) != 4:
        print(
            "Usage: python scripts/assemble_report_payload.py <single|compare> <spec.json> <output.json>",
            file=sys.stderr,
        )
        return 1

    mode, spec_path, output_path = argv[1], argv[2], argv[3]
    spec = _load_json(spec_path)

    if mode == "single":
        payload = _single_payload(spec)
    elif mode == "compare":
        payload = _compare_payload(spec)
    else:
        print("Mode must be single or compare", file=sys.stderr)
        return 1

    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(Path(output_path).resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
