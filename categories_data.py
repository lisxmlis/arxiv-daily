"""根据 arXiv 官方 taxonomy 生成完整 CATEGORIES 字典。"""

from __future__ import annotations

# code -> 中文名（英文官方名见 arxiv taxonomy）
ZH: dict[str, str] = {
    # 一级大类（RSS/API 用 archive 级）
    "cs": "计算机科学（全部）",
    "econ": "经济学（全部）",
    "eess": "电气工程与系统科学（全部）",
    "math": "数学（全部）",
    "physics": "物理学（全部）",
    "q-bio": "定量生物（全部）",
    "q-fin": "定量金融（全部）",
    "stat": "统计学（全部）",
    "astro-ph": "天体物理（全部）",
    "cond-mat": "凝聚态（全部）",
    "nlin": "非线性科学（全部）",
    # CS
    "cs.AI": "人工智能",
    "cs.AR": "硬件体系结构",
    "cs.CC": "计算复杂性",
    "cs.CE": "计算工程/金融/科学",
    "cs.CG": "计算几何",
    "cs.CL": "计算与语言",
    "cs.CR": "密码学与安全",
    "cs.CV": "计算机视觉与模式识别",
    "cs.CY": "计算机与社会",
    "cs.DB": "数据库",
    "cs.DC": "分布式/并行/集群计算",
    "cs.DL": "数字图书馆",
    "cs.DM": "离散数学",
    "cs.DS": "数据结构与算法",
    "cs.ET": "新兴技术",
    "cs.FL": "形式语言与自动机",
    "cs.GL": "一般文献",
    "cs.GR": "图形学",
    "cs.GT": "计算机科学与博弈论",
    "cs.HC": "人机交互",
    "cs.IR": "信息检索",
    "cs.IT": "信息论",
    "cs.LG": "机器学习",
    "cs.LO": "计算机科学中的逻辑",
    "cs.MA": "多智能体系统",
    "cs.MM": "多媒体",
    "cs.MS": "数学软件",
    "cs.NA": "数值分析",
    "cs.NE": "神经网络与进化计算",
    "cs.NI": "网络与互联网体系结构",
    "cs.OH": "其他计算机科学",
    "cs.OS": "操作系统",
    "cs.PF": "性能",
    "cs.PL": "编程语言",
    "cs.RO": "机器人",
    "cs.SC": "符号计算",
    "cs.SD": "声音",
    "cs.SE": "软件工程",
    "cs.SI": "社会与信息网络",
    "cs.SY": "系统与控制",
    # econ
    "econ.EM": "计量经济学",
    "econ.GN": "一般经济学",
    "econ.TH": "理论经济学",
    # eess
    "eess.AS": "音频与语音处理",
    "eess.IV": "图像与视频处理",
    "eess.SP": "信号处理",
    "eess.SY": "系统与控制",
    # math
    "math.AC": "交换代数",
    "math.AG": "代数几何",
    "math.AP": "偏微分方程分析",
    "math.AT": "代数拓扑",
    "math.CA": "经典分析与常微分方程",
    "math.CO": "组合数学",
    "math.CT": "范畴论",
    "math.CV": "复变函数",
    "math.DG": "微分几何",
    "math.DS": "动力系统",
    "math.FA": "泛函分析",
    "math.GM": "一般数学",
    "math.GN": "一般拓扑",
    "math.GR": "群论",
    "math.GT": "几何拓扑",
    "math.HO": "历史与综述",
    "math.IT": "信息论",
    "math.KT": "K 理论与同调",
    "math.LO": "逻辑",
    "math.MG": "度量几何",
    "math.MP": "数学物理",
    "math.NA": "数值分析",
    "math.NT": "数论",
    "math.OA": "算子代数",
    "math.OC": "优化与控制",
    "math.PR": "概率论",
    "math.QA": "量子代数",
    "math.RA": "环与代数",
    "math.RT": "表示论",
    "math.SG": "辛几何",
    "math.SP": "谱理论",
    "math.ST": "统计理论",
    # astro-ph
    "astro-ph.CO": "宇宙学与河外天体物理",
    "astro-ph.EP": "地球与行星天体物理",
    "astro-ph.GA": "星系天体物理",
    "astro-ph.HE": "高能天体物理现象",
    "astro-ph.IM": "天体物理仪器与方法",
    "astro-ph.SR": "太阳与恒星天体物理",
    # cond-mat
    "cond-mat.dis-nn": "无序系统与神经网络",
    "cond-mat.mes-hall": "介观与纳米尺度物理",
    "cond-mat.mtrl-sci": "材料科学",
    "cond-mat.other": "其他凝聚态",
    "cond-mat.quant-gas": "量子气体",
    "cond-mat.soft": "软凝聚态",
    "cond-mat.stat-mech": "统计力学",
    "cond-mat.str-el": "强关联电子",
    "cond-mat.supr-con": "超导",
    # physics singles / other
    "gr-qc": "广义相对论与量子宇宙学",
    "hep-ex": "高能物理-实验",
    "hep-lat": "高能物理-格点",
    "hep-ph": "高能物理-唯象",
    "hep-th": "高能物理-理论",
    "math-ph": "数学物理",
    "nlin.AO": "适应与自组织系统",
    "nlin.CD": "混沌动力学",
    "nlin.CG": "元胞自动机与格子气",
    "nlin.PS": "斑图形成与孤子",
    "nlin.SI": "精确可解与可积系统",
    "nucl-ex": "核实验",
    "nucl-th": "核理论",
    "physics.acc-ph": "加速器物理",
    "physics.ao-ph": "大气与海洋物理",
    "physics.app-ph": "应用物理",
    "physics.atm-clus": "原子与分子团簇",
    "physics.atom-ph": "原子物理",
    "physics.bio-ph": "生物物理",
    "physics.chem-ph": "化学物理",
    "physics.class-ph": "经典物理",
    "physics.comp-ph": "计算物理",
    "physics.data-an": "数据分析/统计与概率",
    "physics.ed-ph": "物理教育",
    "physics.flu-dyn": "流体动力学",
    "physics.gen-ph": "普通物理",
    "physics.geo-ph": "地球物理",
    "physics.hist-ph": "物理史与哲学",
    "physics.ins-det": "仪器与探测器",
    "physics.med-ph": "医学物理",
    "physics.optics": "光学",
    "physics.plasm-ph": "等离子体物理",
    "physics.pop-ph": "科普物理",
    "physics.soc-ph": "物理与社会",
    "physics.space-ph": "空间物理",
    "quant-ph": "量子物理",
    # q-bio
    "q-bio.BM": "生物大分子",
    "q-bio.CB": "细胞行为",
    "q-bio.GN": "基因组学",
    "q-bio.MN": "分子网络",
    "q-bio.NC": "神经元与认知",
    "q-bio.OT": "其他定量生物",
    "q-bio.PE": "种群与进化",
    "q-bio.QM": "定量方法",
    "q-bio.SC": "亚细胞过程",
    "q-bio.TO": "组织与器官",
    # q-fin
    "q-fin.CP": "计算金融",
    "q-fin.EC": "经济学",
    "q-fin.GN": "一般金融",
    "q-fin.MF": "数学金融",
    "q-fin.PM": "投资组合管理",
    "q-fin.PR": "证券定价",
    "q-fin.RM": "风险管理",
    "q-fin.ST": "统计金融",
    "q-fin.TR": "交易与市场微观结构",
    # stat
    "stat.AP": "应用统计",
    "stat.CO": "统计计算",
    "stat.ME": "统计方法",
    "stat.ML": "统计机器学习",
    "stat.OT": "其他统计",
    "stat.TH": "统计理论",
}

# 展示顺序：一级大类在前，再按官方 taxonomy 子类
ARCHIVE_ORDER = [
    "cs",
    "econ",
    "eess",
    "math",
    "astro-ph",
    "cond-mat",
    "gr-qc",
    "hep-ex",
    "hep-lat",
    "hep-ph",
    "hep-th",
    "math-ph",
    "nlin",
    "nucl-ex",
    "nucl-th",
    "physics",
    "quant-ph",
    "q-bio",
    "q-fin",
    "stat",
]

SUBCATEGORY_ORDER = [
    # from official taxonomy dump
    "cs.AI", "cs.AR", "cs.CC", "cs.CE", "cs.CG", "cs.CL", "cs.CR", "cs.CV", "cs.CY",
    "cs.DB", "cs.DC", "cs.DL", "cs.DM", "cs.DS", "cs.ET", "cs.FL", "cs.GL", "cs.GR",
    "cs.GT", "cs.HC", "cs.IR", "cs.IT", "cs.LG", "cs.LO", "cs.MA", "cs.MM", "cs.MS",
    "cs.NA", "cs.NE", "cs.NI", "cs.OH", "cs.OS", "cs.PF", "cs.PL", "cs.RO", "cs.SC",
    "cs.SD", "cs.SE", "cs.SI", "cs.SY",
    "econ.EM", "econ.GN", "econ.TH",
    "eess.AS", "eess.IV", "eess.SP", "eess.SY",
    "math.AC", "math.AG", "math.AP", "math.AT", "math.CA", "math.CO", "math.CT",
    "math.CV", "math.DG", "math.DS", "math.FA", "math.GM", "math.GN", "math.GR",
    "math.GT", "math.HO", "math.IT", "math.KT", "math.LO", "math.MG", "math.MP",
    "math.NA", "math.NT", "math.OA", "math.OC", "math.PR", "math.QA", "math.RA",
    "math.RT", "math.SG", "math.SP", "math.ST",
    "astro-ph.CO", "astro-ph.EP", "astro-ph.GA", "astro-ph.HE", "astro-ph.IM", "astro-ph.SR",
    "cond-mat.dis-nn", "cond-mat.mes-hall", "cond-mat.mtrl-sci", "cond-mat.other",
    "cond-mat.quant-gas", "cond-mat.soft", "cond-mat.stat-mech", "cond-mat.str-el",
    "cond-mat.supr-con",
    "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph",
    "nlin.AO", "nlin.CD", "nlin.CG", "nlin.PS", "nlin.SI",
    "nucl-ex", "nucl-th",
    "physics.acc-ph", "physics.ao-ph", "physics.app-ph", "physics.atm-clus",
    "physics.atom-ph", "physics.bio-ph", "physics.chem-ph", "physics.class-ph",
    "physics.comp-ph", "physics.data-an", "physics.ed-ph", "physics.flu-dyn",
    "physics.gen-ph", "physics.geo-ph", "physics.hist-ph", "physics.ins-det",
    "physics.med-ph", "physics.optics", "physics.plasm-ph", "physics.pop-ph",
    "physics.soc-ph", "physics.space-ph",
    "quant-ph",
    "q-bio.BM", "q-bio.CB", "q-bio.GN", "q-bio.MN", "q-bio.NC", "q-bio.OT",
    "q-bio.PE", "q-bio.QM", "q-bio.SC", "q-bio.TO",
    "q-fin.CP", "q-fin.EC", "q-fin.GN", "q-fin.MF", "q-fin.PM", "q-fin.PR",
    "q-fin.RM", "q-fin.ST", "q-fin.TR",
    "stat.AP", "stat.CO", "stat.ME", "stat.ML", "stat.OT", "stat.TH",
]


def build_categories() -> dict[str, str]:
    """展示名 -> 代码。一级大类在前，再是全部子类。"""
    cats: dict[str, str] = {}
    # 大类快捷项
    for code in ARCHIVE_ORDER:
        if code in ("gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nucl-ex", "nucl-th", "quant-ph"):
            # 这些本身就是叶子/无子类 archive，大类区与子类重复时跳过大类区重复插入
            # 仍放入大类区方便选择
            pass
        zh = ZH.get(code, code)
        label = f"{zh} ({code})"
        cats[label] = code

    # 子类（含无下级的 archive 叶子，会与上面部分重复 label——用同一 label 覆盖即可）
    for code in SUBCATEGORY_ORDER:
        zh = ZH.get(code, code)
        label = f"{zh} ({code})"
        cats[label] = code
    return cats


def build_aliases() -> dict[str, str]:
    aliases = {}
    for code, zh in ZH.items():
        aliases[zh] = code
        aliases[code] = code
    # 常用简称
    aliases.update(
        {
            "凝聚态": "cond-mat",
            "人工智能": "cs.AI",
            "机器学习": "cs.LG",
            "计算机视觉": "cs.CV",
            "量子物理": "quant-ph",
            "高能理论": "hep-th",
            "数学": "math",
            "计算机": "cs",
            "计算机科学": "cs",
            "物理": "physics",
            "物理学": "physics",
            "统计": "stat",
            "天体物理": "astro-ph",
        }
    )
    return aliases


CATEGORIES = build_categories()
CATEGORY_ALIASES = build_aliases()

# 含有子类的一级 archive；API 需用 cat:xxx.*
PARENT_ARCHIVES = {
    "cond-mat",
    "cs",
    "math",
    "astro-ph",
    "physics",
    "nlin",
    "q-bio",
    "q-fin",
    "stat",
    "eess",
    "econ",
}

CATEGORY_GROUPS: dict[str, list[str]] = {
    "常用 / 一级大类": [
        f"{ZH[c]} ({c})" for c in ARCHIVE_ORDER if f"{ZH.get(c, c)} ({c})" in CATEGORIES
    ],
    "计算机科学 cs.*": [k for k, v in CATEGORIES.items() if v.startswith("cs.")],
    "经济学 econ.*": [k for k, v in CATEGORIES.items() if v.startswith("econ.")],
    "电气工程 eess.*": [k for k, v in CATEGORIES.items() if v.startswith("eess.")],
    "数学 math.*": [k for k, v in CATEGORIES.items() if v.startswith("math.")],
    "天体物理 astro-ph.*": [k for k, v in CATEGORIES.items() if v.startswith("astro-ph.")],
    "凝聚态 cond-mat.*": [k for k, v in CATEGORIES.items() if v.startswith("cond-mat.")],
    "高能 / 核 / 引力等": [
        k
        for k, v in CATEGORIES.items()
        if v in {"gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nucl-ex", "nucl-th"}
        or v.startswith("nlin.")
    ],
    "物理学 physics.*": [k for k, v in CATEGORIES.items() if v.startswith("physics.")],
    "量子物理": [k for k, v in CATEGORIES.items() if v == "quant-ph"],
    "定量生物 q-bio.*": [k for k, v in CATEGORIES.items() if v.startswith("q-bio.")],
    "定量金融 q-fin.*": [k for k, v in CATEGORIES.items() if v.startswith("q-fin.")],
    "统计学 stat.*": [k for k, v in CATEGORIES.items() if v.startswith("stat.")],
}
