"""Tài liệu tham khảo."""
from docx.shared import Cm

REFS = [
    'Anderson, M. L. (2014). Subways, strikes, and slowdowns: The impacts of public transit on traffic congestion. American Economic Review, 104(9), 2763–2796.',
    'Beojone, C. V., & Geroliminis, N. (2021). On the inefficiency of ride-sourcing services towards urban congestion. Transportation Research Part C: Emerging Technologies, 124, 102890.',
    'Bureau of Public Roads (1964). Traffic assignment manual. U.S. Department of Commerce, Urban Planning Division.',
    'Cook, C., Kreidieh, A., Vasserman, S., Allcott, H., Arora, N., van Sambeek, F., Tomkins, A., & Turkel, E. (2025). The short-run effects of congestion pricing in New York City (bản sửa: The network-wide effects of congestion pricing: Evidence from New York City). NBER Working Paper No. 33584.',
    'Duranton, G., & Turner, M. A. (2011). The fundamental law of road congestion: Evidence from US cities. American Economic Review, 101(6), 2616–2652.',
    'Gibson, M., & Carnovale, M. (2015). The effects of road pricing on driver behavior and air pollution. Journal of Urban Economics, 89, 62–73.',
    'Green, C. P., Heywood, J. S., & Navarro Paniagua, M. (2020). Did the London congestion charge reduce pollution? Regional Science and Urban Economics, 84, 103573.',
    'Hanna, R., Kreindler, G., & Olken, B. A. (2017). Citywide effects of high-occupancy vehicle restrictions: Evidence from "three-in-one" in Jakarta. Science, 357(6346), 89–93.',
    'Kreindler, G. (2024). Peak-hour road congestion pricing: Experimental evidence and equilibrium implications. Econometrica, 92(4), 1233–1268.',
    'Olszewski, P., & Xie, L. (2005). Modelling the effects of road pricing on traffic in Singapore. Transportation Research Part A: Policy and Practice, 39(7–9), 755–772.',
    'Percoco, M. (2013). Is road pricing effective in abating pollution? Evidence from Milan. Transportation Research Part D: Transport and Environment, 25, 112–118.',
    'Rochet, J.-C., & Tirole, J. (2003). Platform competition in two-sided markets. Journal of the European Economic Association, 1(4), 990–1029.',
    'Santos, G., & Shaffer, B. (2004). Preliminary results of the London congestion charging scheme. Public Works Management & Policy, 9(2), 164–181.',
    'Schaller, B. (2021). Can sharing a ride make for less traffic? Evidence from Uber and Lyft and implications for cities. Transport Policy, 102, 1–10.',
    "Simeonova, E., Currie, J., Nilsson, P., & Walker, R. (2021). Congestion pricing, air pollution, and children's health. Journal of Human Resources, 56(4), 971–996.",
    "Small, K. A., Winston, C., & Yan, J. (2005). Uncovering the distribution of motorists' preferences for travel time and reliability. Econometrica, 73(4), 1367–1382.",
    'Tirachini, A. (2020). Ride-hailing, travel behaviour and sustainable mobility: An international review. Transportation, 47, 2011–2047.',
    'Weyl, E. G., & Fabinger, M. (2013). Pass-through as an economic tool: Principles of incidence under imperfect competition. Journal of Political Economy, 121(3), 528–583.',
    'Abowd, J. M. (2018). The U.S. Census Bureau adopts differential privacy. Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 2867.',
    'Armbrust, M., Xin, R. S., Lian, C., Huai, Y., Liu, D., Bradley, J. K., Meng, X., Kaftan, T., Franklin, M. J., Ghodsi, A., & Zaharia, M. (2015). Spark SQL: Relational data processing in Spark. Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data, 1383–1394.',
    'Armbrust, M., Das, T., Torres, J., Yavuz, B., Zhu, S., Xin, R., Ghodsi, A., Stoica, I., & Zaharia, M. (2018). Structured Streaming: A declarative API for real-time applications in Apache Spark. Proceedings of the 2018 International Conference on Management of Data (SIGMOD), 601–613.',
    'Bloom, H. S. (1995). Minimum detectable effects: A simple way to report the statistical power of experimental designs. Evaluation Review, 19(5), 547–556.',
    'Brodersen, K. H., Gallusser, F., Koehler, J., Remy, N., & Scott, S. L. (2015). Inferring causal impact using Bayesian structural time-series models. Annals of Applied Statistics, 9(1), 247–274.',
    "Castillo, J. C., Knoepfle, D., & Weyl, G. (2017). Surge pricing solves the wild goose chase. Proceedings of the 2017 ACM Conference on Economics and Computation (EC '17), 241–242.",
    'de Montjoye, Y.-A., Hidalgo, C. A., Verleysen, M., & Blondel, V. D. (2013). Unique in the crowd: The privacy bounds of human mobility. Scientific Reports, 3, 1376.',
    'Douriez, M., Doraiswamy, H., Freire, J., & Silva, C. T. (2016). Anonymizing NYC taxi data: Does it matter? Proceedings of the 2016 IEEE International Conference on Data Science and Advanced Analytics (DSAA), 140–148.',
    'Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006). Calibrating noise to sensitivity in private data analysis. Theory of Cryptography Conference (TCC 2006), Lecture Notes in Computer Science 3876, 265–284.',
    'Dwork, C., & Roth, A. (2014). The algorithmic foundations of differential privacy. Foundations and Trends in Theoretical Computer Science, 9(3–4), 211–407.',
    'Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and practice (3rd ed.). OTexts.',
    'Kohavi, R., Tang, D., & Xu, Y. (2020). Trustworthy online controlled experiments: A practical guide to A/B testing. Cambridge University Press.',
    'Laney, D. B. (2002). Improved control charts for attributes. Quality Engineering, 14(4), 531–537.',
    'Laney, D. B. (2017). Infonomics: How to monetize, manage, and measure information as an asset for competitive advantage. Bibliomotion (Routledge).',
    'Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation forest. Proceedings of the 2008 Eighth IEEE International Conference on Data Mining (ICDM), 413–422.',
    'Montgomery, D. C. (2019). Introduction to statistical quality control (8th ed.). Wiley.',
    'Moody, D., & Walsh, P. (1999). Measuring the value of information: An asset valuation approach. Proceedings of the Seventh European Conference on Information Systems (ECIS).',
    'Rose, S., Borchert, O., Mitchell, S., & Connelly, S. (2020). Zero trust architecture (NIST Special Publication 800-207). National Institute of Standards and Technology.',
    'Sweeney, L. (2002). k-anonymity: A model for protecting privacy. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), 557–570.',
    'Zaharia, M., Chowdhury, M., Das, T., Dave, A., Ma, J., McCauley, M., Franklin, M. J., Shenker, S., & Stoica, I. (2012). Resilient distributed datasets: A fault-tolerant abstraction for in-memory cluster computing. Proceedings of the 9th USENIX Symposium on Networked Systems Design and Implementation (NSDI), 15–28.',
    "Abadie, A. (2021). Using synthetic controls: Feasibility, data requirements, and methodological aspects. Journal of Economic Literature, 59(2), 391–425.",
    "Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control methods for comparative case studies: Estimating the effect of California's tobacco control program. Journal of the American Statistical Association, 105(490), 493–505.",
    "Angrist, J. D., & Pischke, J.-S. (2009). Mostly harmless econometrics: An empiricist's companion. Princeton University Press.",
    "Armbrust, M., Ghodsi, A., Xin, R., & Zaharia, M. (2021). Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. Proceedings of the Conference on Innovative Data Systems Research (CIDR).",
    "Athey, S., & Imbens, G. W. (2017). The state of applied econometrics: Causality and policy evaluation. Journal of Economic Perspectives, 31(2), 3–32.",
    "Bertrand, M., Duflo, E., & Mullainathan, S. (2004). How much should we trust differences-in-differences estimates? Quarterly Journal of Economics, 119(1), 249–275.",
    "Börjesson, M., Eliasson, J., Hugosson, M. B., & Brundell-Freij, K. (2012). The Stockholm congestion charges—5 years on. Effects, acceptability and lessons learnt. Transport Policy, 20, 1–12.",
    "Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. Journal of Econometrics, 225(2), 200–230.",
    "Cameron, A. C., & Miller, D. L. (2015). A practitioner's guide to cluster-robust inference. Journal of Human Resources, 50(2), 317–372.",
    "Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters. The Econometrics Journal, 21(1), C1–C68.",
    "Chernozhukov, V., Demirer, M., Duflo, E., & Fernández-Val, I. (2018). Generic machine learning inference on heterogeneous treatment effects in randomized experiments. NBER Working Paper No. 24678.",
    "Cohen, P., Hahn, R., Hall, J., Levitt, S., & Metcalfe, R. (2016). Using big data to estimate consumer surplus: The case of Uber. NBER Working Paper No. 22627.",
    "Correia, S. (2016). Linear models with high-dimensional fixed effects: An efficient and feasible estimator. Working paper, Duke University.",
    "Cramer, J., & Krueger, A. B. (2016). Disruptive change in the taxi business: The case of Uber. American Economic Review, 106(5), 177–182.",
    "Dean, J., & Ghemawat, S. (2008). MapReduce: Simplified data processing on large clusters. Communications of the ACM, 51(1), 107–113.",
    "Eliasson, J. (2009). A cost–benefit analysis of the Stockholm congestion charging system. Transportation Research Part A: Policy and Practice, 43(4), 468–480.",
    "Erhardt, G. D., Roy, S., Cooper, D., Sana, B., Chen, M., & Castiglione, J. (2019). Do transportation network companies decrease or increase congestion? Science Advances, 5(5), eaau2670.",
    "Ferman, B., & Pinto, C. (2021). Synthetic controls with imperfect pretreatment fit. Quantitative Economics, 12(4), 1197–1221.",
    "Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. Journal of Econometrics, 225(2), 254–277.",
    "Guimarães, P., & Portugal, P. (2010). A simple feasible procedure to fit models with high-dimensional fixed effects. The Stata Journal, 10(4), 628–649.",
    "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems, 30.",
    "Kennedy, E. H. (2023). Towards optimal doubly robust estimation of heterogeneous causal effects. Electronic Journal of Statistics, 17(2), 3008–3049.",
    "Leape, J. (2006). The London congestion charge. Journal of Economic Perspectives, 20(4), 157–176.",
    "Melnik, S., Gubarev, A., Long, J. J., Romer, G., Shivakumar, S., Tolton, M., & Vassilakis, T. (2010). Dremel: Interactive analysis of web-scale datasets. Proceedings of the VLDB Endowment, 3(1–2), 330–339.",
    "Metropolitan Transportation Authority (2025). Congestion Relief Zone tolls: Taxis and for-hire vehicles. https://www.mta.info/fares-tolls/tolls/congestion-relief-zone/taxi-fhv-tolls (truy cập 09/2026).",
    "New York City Taxi and Limousine Commission (2026). TLC Trip Record Data. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page (truy cập 09/2026).",
    "New York City Taxi and Limousine Commission (2025). Data dictionary – High Volume FHV trip records. https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_hvfhs.pdf.",
    "Nguyễn Thôn Dã (2026). Bài giảng Nghiên cứu Dữ liệu lớn trong kinh doanh, Chương 1–7. Trường Đại học Kinh tế – Luật, ĐHQG TP.HCM.",
    "Pandey, A., Guler, I., & Gayah, V. (2026). The effect of the New York City congestion toll on trips served by transportation network companies. Findings. https://doi.org/10.32866/001c.155761.",
    "Pigou, A. C. (1920). The economics of welfare. Macmillan.",
    "Raasveldt, M., & Mühleisen, H. (2019). DuckDB: An embeddable analytical database. Proceedings of the 2019 International Conference on Management of Data (SIGMOD), 1981–1984.",
    "Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. Review of Economic Studies, 90(5), 2555–2591.",
    "Roth, J., Sant'Anna, P. H. C., Bilinski, A., & Poe, J. (2023). What's trending in difference-in-differences? A synthesis of the recent econometrics literature. Journal of Econometrics, 235(2), 2218–2244.",
    "Small, K. A., & Verhoef, E. T. (2007). The economics of urban transportation. Routledge.",
    "Vickrey, W. S. (1969). Congestion theory and transport investment. American Economic Review, 59(2), 251–260.",
    "Walters, A. A. (1961). The theory and measurement of private and social cost of highway congestion. Econometrica, 29(4), 676–699.",
    "Wang, R. Y., & Strong, D. M. (1996). Beyond accuracy: What data quality means to data consumers. Journal of Management Information Systems, 12(4), 5–33.",
    "Zaharia, M., Xin, R. S., Wendell, P., Das, T., Armbrust, M., Dave, A., Meng, X., Rosen, J., Venkataraman, S., Franklin, M. J., Ghodsi, A., Gonzalez, J., Shenker, S., & Stoica, I. (2016). Apache Spark: A unified engine for big data processing. Communications of the ACM, 59(11), 56–65.",
]


def _key(r):
    import unicodedata
    k = unicodedata.normalize("NFD", r).encode("ascii", "ignore").decode().lower()
    return k


def build(rp, R):
    rp.H1("TÀI LIỆU THAM KHẢO", numbered=False)
    for i, r in enumerate(sorted(REFS, key=_key), 1):
        p = rp.P(f"[{i}] {r}", indent=False, align="left", size=12)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.line_spacing = 1.2
