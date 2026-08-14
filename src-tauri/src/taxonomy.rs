//! Structured UPSC syllabus taxonomy used by the offline question index.
//!
//! Every indexed question receives exactly one main tag and at most three
//! subtags. The labels follow the UPSC CSE syllabus rather than a generic
//! document taxonomy, so they can also act as useful retrieval concepts.

pub const MAX_SUBTAGS: usize = 3;

#[derive(Debug, Clone, Copy)]
pub struct UpscSubtag {
    pub name: &'static str,
    pub description: &'static str,
}

#[derive(Debug, Clone, Copy)]
pub struct UpscMainTag {
    pub name: &'static str,
    pub description: &'static str,
    pub subtags: &'static [UpscSubtag],
}

const ART_CULTURE: &[UpscSubtag] = &[
    UpscSubtag { name: "Architecture, Sculpture & Archaeology", description: "Indian architecture, temples, stupas, caves, sculpture, inscriptions, archaeology and material heritage" },
    UpscSubtag { name: "Literature, Languages & Philosophy", description: "Indian literature, classical and regional languages, texts, schools of philosophy and intellectual traditions" },
    UpscSubtag { name: "Religion & Bhakti-Sufi Traditions", description: "Indian religions, sects, saints, reform traditions, Bhakti, Sufism, Buddhism and Jainism" },
    UpscSubtag { name: "Music, Dance, Theatre & Festivals", description: "Classical and folk music, dance, theatre, puppetry, festivals and performing arts" },
    UpscSubtag { name: "Paintings, Crafts & Cultural Heritage", description: "Indian paintings, handicrafts, textiles, cultural institutions, heritage sites and conservation" },
];

const HISTORY: &[UpscSubtag] = &[
    UpscSubtag { name: "Ancient India", description: "Prehistory, Indus civilisation, Vedic age, ancient kingdoms, empires, society and economy" },
    UpscSubtag { name: "Medieval India", description: "Early medieval kingdoms, Delhi Sultanate, Vijayanagara, Mughals, regional states, society and economy" },
    UpscSubtag { name: "Modern India & Freedom Struggle", description: "British expansion, colonial economy, social reform, nationalism, freedom movement and independence" },
    UpscSubtag { name: "Post-Independence India", description: "Consolidation, reorganisation, political and socioeconomic developments in India after 1947" },
    UpscSubtag { name: "World History", description: "Industrial revolution, world wars, colonisation, decolonisation, political ideologies and global social change" },
    UpscSubtag { name: "Historical Sources & Personalities", description: "Travellers, chronicles, inscriptions, literature, historians, leaders and important historical personalities" },
];

const GEOGRAPHY: &[UpscSubtag] = &[
    UpscSubtag { name: "Physical Geography & Geomorphology", description: "Earth structure, rocks, landforms, plate tectonics, earthquakes, volcanoes and geomorphic processes" },
    UpscSubtag { name: "Climate & Weather", description: "Atmosphere, monsoon, winds, rainfall, cyclones, climate systems and weather phenomena" },
    UpscSubtag { name: "Indian Geography", description: "India's physiography, location, regional geography, natural resources and spatial patterns" },
    UpscSubtag { name: "Rivers, Lakes & Water Resources", description: "River systems, drainage, lakes, groundwater, watersheds, dams, irrigation and water management" },
    UpscSubtag { name: "Oceans, Coasts & Islands", description: "Oceanography, seas, currents, marine resources, coasts, ports, islands and coastal processes" },
    UpscSubtag { name: "Population & Settlements", description: "Population, demography, migration, settlements, urbanisation, cities and human geography" },
    UpscSubtag { name: "Resources, Industries & Transport", description: "Minerals, energy resources, industries, industrial location, transport, trade routes and infrastructure" },
    UpscSubtag { name: "World Geography & Places", description: "Continents, countries, regions, international rivers, mountains and places of geographic importance" },
    UpscSubtag { name: "Maps & Location", description: "Map-based location, borders, spatial relationships, latitudes, longitudes and geographic matching" },
];

const SOCIETY: &[UpscSubtag] = &[
    UpscSubtag { name: "Diversity, Caste & Communalism", description: "Indian diversity, caste, religion, regionalism, secularism, communalism and social cohesion" },
    UpscSubtag { name: "Women & Gender", description: "Women, gender equality, patriarchy, representation, violence, work and women's organisations" },
    UpscSubtag { name: "Population & Demography", description: "Population trends, demographic dividend, ageing, fertility, mortality and migration" },
    UpscSubtag { name: "Poverty, Urbanisation & Development", description: "Poverty, inequality, urbanisation, slums, development outcomes and social problems" },
    UpscSubtag { name: "Globalisation & Social Change", description: "Effects of globalisation, modernisation, technology and economic change on Indian society" },
    UpscSubtag { name: "Social Empowerment", description: "Empowerment, inclusion and issues of disadvantaged, marginalised and vulnerable communities" },
];

const POLITY: &[UpscSubtag] = &[
    UpscSubtag { name: "Constitutional Framework & Amendments", description: "Constitution, basic structure, amendments, schedules, constitutionalism and comparative constitutions" },
    UpscSubtag { name: "Fundamental Rights, DPSP & Duties", description: "Fundamental rights, directive principles, fundamental duties, citizenship and constitutional remedies" },
    UpscSubtag { name: "Parliament & State Legislatures", description: "Parliament, legislatures, bills, committees, privileges, procedures and legislative accountability" },
    UpscSubtag { name: "Executive & Public Administration", description: "President, Governor, Prime Minister, Council of Ministers and Union or State administration" },
    UpscSubtag { name: "Judiciary & Legal System", description: "Supreme Court, High Courts, judicial review, tribunals, legal aid and justice system" },
    UpscSubtag { name: "Federalism & Local Government", description: "Centre-State relations, federal structure, inter-state relations, Panchayats and municipalities" },
    UpscSubtag { name: "Elections & Political Process", description: "Election Commission, electoral system, political parties, representation and anti-defection" },
    UpscSubtag { name: "Constitutional & Statutory Bodies", description: "Constitutional, statutory, regulatory and quasi-judicial bodies, commissions and authorities" },
];

const GOVERNANCE: &[UpscSubtag] = &[
    UpscSubtag { name: "Transparency, Accountability & RTI", description: "Transparency, accountability, Right to Information, audits, oversight and institutional checks" },
    UpscSubtag { name: "E-Governance & Digital Public Services", description: "Digital governance, technology platforms, digital public infrastructure and electronic service delivery" },
    UpscSubtag { name: "Civil Services & Administrative Reforms", description: "Civil services, bureaucracy, capacity building, administrative law and institutional reform" },
    UpscSubtag { name: "Government Policies & Implementation", description: "Policy design, implementation, evaluation, interventions, missions, schemes and implementation gaps" },
    UpscSubtag { name: "NGOs, SHGs & Pressure Groups", description: "Non-government organisations, self-help groups, associations, pressure groups and stakeholders" },
    UpscSubtag { name: "Citizen Charters & Service Delivery", description: "Citizen charters, grievance redressal, public services, participation and last-mile delivery" },
];

const SOCIAL_JUSTICE: &[UpscSubtag] = &[
    UpscSubtag { name: "Health, Nutrition & Sanitation", description: "Public health, healthcare, disease, nutrition, sanitation, maternal and child welfare" },
    UpscSubtag { name: "Education & Human Resources", description: "Education policy, schools, higher education, skills, literacy and human resource development" },
    UpscSubtag { name: "Welfare Schemes & Vulnerable Sections", description: "Welfare programmes and issues concerning children, elderly, disabled, minorities, SCs, STs and OBCs" },
    UpscSubtag { name: "Poverty, Hunger & Inclusion", description: "Poverty, hunger, inequality, social inclusion, basic services and inclusive development" },
    UpscSubtag { name: "Labour, Employment & Rights", description: "Labour welfare, employment, informal workers, migration, social security and workplace rights" },
    UpscSubtag { name: "Human Rights & Social Protection", description: "Human rights institutions, protection laws, social assistance and rights-based welfare" },
];

const INTERNATIONAL_RELATIONS: &[UpscSubtag] = &[
    UpscSubtag { name: "India & Its Neighbourhood", description: "India's relations with neighbouring countries, border regions and neighbourhood policy" },
    UpscSubtag { name: "Bilateral Relations", description: "India's bilateral political, economic, strategic and cultural relations with other countries" },
    UpscSubtag { name: "Regional & Global Groupings", description: "Regional blocs, strategic groupings, multilateral forums and their agreements affecting India" },
    UpscSubtag { name: "International Institutions & Agreements", description: "United Nations, international organisations, treaties, conventions, global governance and institutions" },
    UpscSubtag { name: "Foreign Policy & Diplomacy", description: "Indian foreign policy, diplomacy, strategic autonomy, soft power and international engagement" },
    UpscSubtag { name: "Diaspora & Global Issues", description: "Indian diaspora and transnational issues including migration, development and humanitarian concerns" },
    UpscSubtag { name: "Geopolitics & Conflict", description: "Wars, conflicts, disputed regions, great-power competition, maritime geopolitics and strategic affairs" },
];

const ECONOMY: &[UpscSubtag] = &[
    UpscSubtag { name: "Growth, Development & Employment", description: "Economic growth, development, poverty, inequality, jobs, productivity and human development" },
    UpscSubtag { name: "Fiscal Policy, Budgeting & Taxation", description: "Government budget, fiscal policy, deficits, public expenditure, taxation and fiscal federalism" },
    UpscSubtag { name: "Monetary Policy, Banking & Inflation", description: "Reserve Bank, monetary policy, banks, credit, interest rates, money supply and inflation" },
    UpscSubtag { name: "External Sector, Trade & Balance of Payments", description: "Foreign trade, exchange rates, balance of payments, capital flows and external debt" },
    UpscSubtag { name: "Infrastructure & Investment", description: "Energy, transport, logistics, housing, infrastructure finance, investment models and public-private partnerships" },
    UpscSubtag { name: "Industry, MSMEs & Services", description: "Industrial policy, manufacturing, MSMEs, services, startups, business environment and production" },
    UpscSubtag { name: "Financial Markets & Inclusion", description: "Capital markets, bonds, insurance, pensions, fintech, financial instruments and financial inclusion" },
    UpscSubtag { name: "Planning, Reforms & Public Finance", description: "Economic planning, liberalisation, structural reforms, resource mobilisation and public finance" },
];

const AGRICULTURE: &[UpscSubtag] = &[
    UpscSubtag { name: "Cropping Patterns & Agro-Climatic Regions", description: "Crops, cropping patterns, seasons, soils, agro-climatic conditions and regional agriculture" },
    UpscSubtag { name: "Irrigation & Water Management", description: "Irrigation systems, watershed development, groundwater, micro-irrigation and farm water use" },
    UpscSubtag { name: "Agricultural Inputs, Technology & Extension", description: "Seeds, fertilisers, farm machinery, biotechnology, extension, digital agriculture and productivity" },
    UpscSubtag { name: "MSP, Markets & Food Supply Chains", description: "Minimum support price, mandis, marketing, storage, transport, food processing and supply chains" },
    UpscSubtag { name: "Food Security & Public Distribution", description: "Food security, buffer stocks, procurement, public distribution and nutrition support" },
    UpscSubtag { name: "Animal Husbandry, Fisheries & Forestry", description: "Livestock, dairy, fisheries, aquaculture, veterinary issues, farm forestry and allied sectors" },
    UpscSubtag { name: "Land Reforms & Farm Institutions", description: "Land reforms, tenancy, holdings, farmer organisations, cooperatives, credit and crop insurance" },
];

const SCIENCE_TECHNOLOGY: &[UpscSubtag] = &[
    UpscSubtag { name: "Space Technology", description: "Satellites, launch vehicles, space missions, astronomy, remote sensing and navigation systems" },
    UpscSubtag { name: "Defence & Nuclear Technology", description: "Missiles, defence systems, military technology, nuclear energy, reactors and atomic science" },
    UpscSubtag { name: "Information Technology, AI & Robotics", description: "Computing, internet, semiconductors, artificial intelligence, robotics, cybersecurity technology and digital systems" },
    UpscSubtag { name: "Biotechnology & Genetic Engineering", description: "Genetics, DNA, biotechnology, gene editing, cloning, stem cells and biological applications" },
    UpscSubtag { name: "Health, Medicine & Public Science", description: "Medicine, vaccines, diagnostics, diseases, pharmaceuticals, human biology and health technologies" },
    UpscSubtag { name: "Energy Technology", description: "Hydrogen, batteries, solar, wind, biofuels, energy storage and clean-energy technology" },
    UpscSubtag { name: "Basic Physics, Chemistry & Biology", description: "Fundamental scientific principles, materials, chemicals, organisms, physiology and everyday science" },
    UpscSubtag { name: "Emerging Technologies & Innovation", description: "Nanotechnology, quantum technology, advanced materials, intellectual property and innovation policy" },
];

const ENVIRONMENT: &[UpscSubtag] = &[
    UpscSubtag { name: "Ecology, Ecosystems & Biodiversity", description: "Ecological principles, ecosystems, habitats, food chains, biodiversity and ecosystem services" },
    UpscSubtag { name: "Climate Change & Carbon Management", description: "Global warming, greenhouse gases, carbon markets, mitigation, adaptation and climate finance" },
    UpscSubtag { name: "Pollution & Waste Management", description: "Air, water, soil and noise pollution, chemicals, plastics, sewage and solid waste management" },
    UpscSubtag { name: "Conservation, Protected Areas & Species", description: "Wildlife, endangered species, protected areas, conservation programmes and human-wildlife conflict" },
    UpscSubtag { name: "Environmental Laws, Bodies & Conventions", description: "Environmental laws, institutions, assessments, international conventions and regulatory frameworks" },
    UpscSubtag { name: "Forests, Wetlands & Coastal Ecology", description: "Forests, mangroves, wetlands, coral reefs, coastal and marine ecology and restoration" },
    UpscSubtag { name: "Renewable Energy & Sustainable Development", description: "Renewable energy, resource efficiency, circular economy and sustainable development goals" },
];

const DISASTER_MANAGEMENT: &[UpscSubtag] = &[
    UpscSubtag { name: "Natural Hazards", description: "Floods, droughts, cyclones, earthquakes, landslides, tsunamis, heatwaves and natural hazards" },
    UpscSubtag { name: "Disaster Preparedness & Risk Reduction", description: "Risk assessment, early warning, prevention, mitigation, preparedness and resilient infrastructure" },
    UpscSubtag { name: "Response, Relief & Rehabilitation", description: "Emergency response, relief, recovery, reconstruction and rehabilitation after disasters" },
    UpscSubtag { name: "Urban & Industrial Disasters", description: "Urban flooding, fires, industrial accidents, chemical hazards and technological disasters" },
    UpscSubtag { name: "Institutions & Community Resilience", description: "Disaster laws, NDMA, institutions, financing, local participation and community resilience" },
];

const INTERNAL_SECURITY: &[UpscSubtag] = &[
    UpscSubtag { name: "Terrorism, Insurgency & Extremism", description: "Terrorism, insurgency, left-wing extremism, separatism, radicalisation and counter-terrorism" },
    UpscSubtag { name: "Border & Coastal Security", description: "Land borders, coastal security, infiltration, smuggling, border management and border infrastructure" },
    UpscSubtag { name: "Cyber Security & Communication Networks", description: "Cyber threats, critical infrastructure, data security, communication networks and cyber warfare" },
    UpscSubtag { name: "Organised Crime, Money Laundering & Trafficking", description: "Organised crime, terror financing, money laundering, drugs, arms and human trafficking" },
    UpscSubtag { name: "Security Forces, Agencies & Intelligence", description: "Police, armed forces, paramilitary forces, intelligence agencies, mandates and security coordination" },
    UpscSubtag { name: "Media, Radicalisation & Security Challenges", description: "Social media, misinformation, radicalisation, communal violence and emerging internal security challenges" },
    UpscSubtag { name: "Defence Preparedness", description: "National security strategy, defence preparedness, military modernisation and civil-military coordination" },
];

const ETHICS: &[UpscSubtag] = &[
    UpscSubtag { name: "Ethics & Human Interface", description: "Ethics, morality, values, determinants and consequences of ethical action in human conduct" },
    UpscSubtag { name: "Attitude & Behaviour", description: "Attitude, persuasion, prejudice, behaviour, social influence and moral or political attitudes" },
    UpscSubtag { name: "Aptitude & Foundational Values", description: "Integrity, impartiality, objectivity, non-partisanship, empathy, tolerance and compassion" },
    UpscSubtag { name: "Emotional Intelligence", description: "Emotional intelligence concepts, administration, leadership, self-awareness and interpersonal effectiveness" },
    UpscSubtag { name: "Moral Thinkers & Philosophers", description: "Indian and global moral thinkers, philosophers, teachings and ethical theories" },
    UpscSubtag { name: "Public Service Values & Civil Service Ethics", description: "Civil service values, ethical dilemmas, conscience, accountability and ethics in public administration" },
    UpscSubtag { name: "Probity, Corruption & Accountability", description: "Probity, corruption, codes of ethics, transparency, public funds and corporate governance" },
    UpscSubtag { name: "Applied Ethics & Case Studies", description: "Administrative case studies, competing values, stakeholder analysis and ethical decision-making" },
];

const CURRENT_EVENTS: &[UpscSubtag] = &[
    UpscSubtag { name: "Awards, Honours & Personalities", description: "National and international awards, honours, notable persons and major appointments" },
    UpscSubtag { name: "Sports", description: "Sports events, tournaments, trophies, athletes, rules and sporting institutions" },
    UpscSubtag { name: "Reports, Indices & Rankings", description: "Major reports, indices, rankings, surveys and the organisations that publish them" },
    UpscSubtag { name: "Places & Events in Focus", description: "Important places, events and developments of national or international significance" },
    UpscSubtag { name: "Organisations & Initiatives", description: "New organisations, campaigns, programmes and initiatives not confined to another syllabus domain" },
];

const ESSAY: &[UpscSubtag] = &[
    UpscSubtag { name: "Philosophy, Ideas & Human Values", description: "Abstract ideas, wisdom, truth, knowledge, values, character, freedom and the human condition" },
    UpscSubtag { name: "Society & Social Change", description: "Society, culture, family, gender, inequality, identity and processes of social change" },
    UpscSubtag { name: "Democracy, Justice & Governance", description: "Democracy, justice, liberty, institutions, leadership, governance and citizenship" },
    UpscSubtag { name: "Education & Human Development", description: "Education, learning, youth, creativity, health, capabilities and human development" },
    UpscSubtag { name: "Economy, Growth & Development", description: "Economic choices, work, poverty, prosperity, inclusive growth and development models" },
    UpscSubtag { name: "Science, Technology & Innovation", description: "Science, technology, innovation, media, digital change and their effects on humanity" },
    UpscSubtag { name: "Environment & Sustainability", description: "Nature, environment, climate, sustainability and intergenerational responsibility" },
    UpscSubtag { name: "Peace, Conflict & Globalisation", description: "Peace, war, power, international order, globalisation and global interdependence" },
];

const CSAT: &[UpscSubtag] = &[
    UpscSubtag { name: "Reading Comprehension", description: "Passages, inference, central idea, assumptions, arguments and verbal comprehension" },
    UpscSubtag { name: "Logical Reasoning", description: "Logical deduction, statements, conclusions, syllogisms, arrangements and reasoning puzzles" },
    UpscSubtag { name: "Analytical Ability", description: "Analytical reasoning, data sufficiency, patterns, relationships and structured problem analysis" },
    UpscSubtag { name: "Basic Numeracy", description: "Numbers, arithmetic, algebra, ratios, percentages, averages, time, work and quantitative aptitude" },
    UpscSubtag { name: "Data Interpretation", description: "Tables, charts, graphs, quantitative data comparison and numerical interpretation" },
    UpscSubtag { name: "Decision Making & Problem Solving", description: "Situational judgement, decision-making, problem-solving and evaluation of courses of action" },
    UpscSubtag { name: "Interpersonal & Communication Skills", description: "Communication, interpersonal understanding, collaboration and social situations" },
];

const MATHEMATICS: &[UpscSubtag] = &[
    UpscSubtag { name: "Linear Algebra", description: "Vector spaces, matrices, determinants, linear transformations, eigenvalues and canonical forms" },
    UpscSubtag { name: "Calculus", description: "Limits, continuity, differentiation, integration, multivariable calculus and applications" },
    UpscSubtag { name: "Analytic Geometry", description: "Cartesian and three-dimensional geometry, conics, planes, lines and quadric surfaces" },
    UpscSubtag { name: "Ordinary Differential Equations", description: "First and higher-order ordinary differential equations, existence, solutions and applications" },
    UpscSubtag { name: "Dynamics & Statics", description: "Particle dynamics, projectiles, constraints, equilibrium, friction, virtual work and stability" },
    UpscSubtag { name: "Vector Analysis", description: "Vector fields, gradient, divergence, curl, line and surface integrals and integral theorems" },
    UpscSubtag { name: "Abstract Algebra", description: "Groups, subgroups, homomorphisms, rings, ideals, fields and algebraic structures" },
    UpscSubtag { name: "Real Analysis", description: "Sequences, series, metric spaces, continuity, differentiation, integration and convergence" },
    UpscSubtag { name: "Complex Analysis", description: "Analytic functions, contour integration, series, residues and conformal mappings" },
    UpscSubtag { name: "Linear Programming", description: "Linear programming problems, simplex method, duality, transportation and assignment" },
    UpscSubtag { name: "Partial Differential Equations", description: "First and second-order partial differential equations, characteristics and boundary-value problems" },
    UpscSubtag { name: "Numerical Analysis & Computer Programming", description: "Numerical methods, errors, interpolation, numerical integration, algorithms and computer programming" },
    UpscSubtag { name: "Mechanics & Fluid Dynamics", description: "Generalised mechanics, rigid bodies, fluid kinematics, fluid equations, waves and viscous flow" },
];

pub const UPSC_MAIN_TAGS: &[UpscMainTag] = &[
    UpscMainTag { name: "Art & Culture", description: "Indian art forms, architecture, literature, religion, philosophy and cultural heritage", subtags: ART_CULTURE },
    UpscMainTag { name: "History", description: "Ancient, medieval, modern, post-independence and world history", subtags: HISTORY },
    UpscMainTag { name: "Geography", description: "Physical, Indian, human and world geography, resources and spatial relationships", subtags: GEOGRAPHY },
    UpscMainTag { name: "Indian Society", description: "Indian society, diversity, population, social change, inequality and empowerment", subtags: SOCIETY },
    UpscMainTag { name: "Polity & Constitution", description: "Indian Constitution, political institutions, rights, federalism, elections and law", subtags: POLITY },
    UpscMainTag { name: "Governance", description: "Governance, public administration, accountability, e-governance and policy implementation", subtags: GOVERNANCE },
    UpscMainTag { name: "Social Justice", description: "Welfare, health, education, vulnerable sections, inclusion and human rights", subtags: SOCIAL_JUSTICE },
    UpscMainTag { name: "International Relations", description: "India's foreign relations, international institutions, groupings, agreements and geopolitics", subtags: INTERNATIONAL_RELATIONS },
    UpscMainTag { name: "Economy", description: "Indian economy, growth, finance, banking, budgeting, trade, infrastructure and reforms", subtags: ECONOMY },
    UpscMainTag { name: "Agriculture", description: "Indian agriculture, crops, irrigation, farm policy, food security and allied sectors", subtags: AGRICULTURE },
    UpscMainTag { name: "Science & Technology", description: "Science, technology, space, defence, health, biotechnology, energy and innovation", subtags: SCIENCE_TECHNOLOGY },
    UpscMainTag { name: "Environment & Ecology", description: "Ecology, biodiversity, conservation, pollution, climate change and sustainability", subtags: ENVIRONMENT },
    UpscMainTag { name: "Disaster Management", description: "Disaster hazards, risk reduction, preparedness, response and resilient recovery", subtags: DISASTER_MANAGEMENT },
    UpscMainTag { name: "Internal Security", description: "Terrorism, extremism, borders, cyber threats, organised crime and security institutions", subtags: INTERNAL_SECURITY },
    UpscMainTag { name: "Ethics, Integrity & Aptitude", description: "Ethics, attitude, integrity, public service values, probity and ethical case studies", subtags: ETHICS },
    UpscMainTag { name: "Current Events", description: "Awards, sports, reports, personalities and significant contemporary events", subtags: CURRENT_EVENTS },
    UpscMainTag { name: "Essay & Philosophical Themes", description: "Philosophical and interdisciplinary essay themes involving ideas, values and society", subtags: ESSAY },
    UpscMainTag { name: "CSAT", description: "Civil Services Aptitude Test comprehension, reasoning, numeracy, data and decision-making", subtags: CSAT },
    UpscMainTag { name: "Mathematics", description: "UPSC Mathematics Optional Paper I and Paper II syllabus", subtags: MATHEMATICS },
];

const PRELIMS_GS_TAGS: &[&str] = &[
    "Art & Culture",
    "History",
    "Geography",
    "Indian Society",
    "Polity & Constitution",
    "Governance",
    "Social Justice",
    "International Relations",
    "Economy",
    "Agriculture",
    "Science & Technology",
    "Environment & Ecology",
    "Disaster Management",
    "Internal Security",
    "Current Events",
];
const MAINS_GS1_TAGS: &[&str] = &["Art & Culture", "History", "Geography", "Indian Society"];
const MAINS_GS2_TAGS: &[&str] = &[
    "Polity & Constitution",
    "Governance",
    "Social Justice",
    "International Relations",
];
const MAINS_GS3_TAGS: &[&str] = &[
    "Economy",
    "Agriculture",
    "Science & Technology",
    "Environment & Ecology",
    "Disaster Management",
    "Internal Security",
];
const MAINS_GS4_TAGS: &[&str] = &["Ethics, Integrity & Aptitude"];
const ESSAY_TAGS: &[&str] = &[
    "Essay & Philosophical Themes",
    "Art & Culture",
    "History",
    "Geography",
    "Indian Society",
    "Polity & Constitution",
    "Governance",
    "Social Justice",
    "International Relations",
    "Economy",
    "Agriculture",
    "Science & Technology",
    "Environment & Ecology",
    "Disaster Management",
    "Internal Security",
    "Ethics, Integrity & Aptitude",
];
const CSAT_TAGS: &[&str] = &["CSAT"];
const MATHS_TAGS: &[&str] = &["Mathematics"];

pub fn main_tags_for_section(section: &str) -> Option<Vec<&'static UpscMainTag>> {
    let allowed = match section {
        "prelims-gs1" => PRELIMS_GS_TAGS,
        "mains-gs1" => MAINS_GS1_TAGS,
        "mains-gs2" => MAINS_GS2_TAGS,
        "mains-gs3" => MAINS_GS3_TAGS,
        "mains-gs4" => MAINS_GS4_TAGS,
        "mains-essay" => ESSAY_TAGS,
        "prelims-csat" => CSAT_TAGS,
        "mains-maths1" | "mains-maths2" => MATHS_TAGS,
        _ => return None,
    };
    Some(allowed.iter().filter_map(|name| main_tag(name)).collect())
}

pub fn main_tag(name: &str) -> Option<&'static UpscMainTag> {
    UPSC_MAIN_TAGS.iter().find(|tag| tag.name == name)
}

pub fn retrieval_text(main: &str, subtags: &[String]) -> String {
    let Some(main_definition) = main_tag(main) else {
        return std::iter::once(main)
            .chain(subtags.iter().map(String::as_str))
            .collect::<Vec<_>>()
            .join(" ");
    };
    let mut parts = vec![main_definition.name, main_definition.description];
    for subtag in subtags.iter().take(MAX_SUBTAGS) {
        if let Some(definition) = main_definition
            .subtags
            .iter()
            .find(|definition| definition.name == subtag)
        {
            parts.push(definition.name);
            parts.push(definition.description);
        }
    }
    parts.join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn taxonomy_has_unique_main_and_subtag_names() {
        let mut main_names = HashSet::new();
        for main in UPSC_MAIN_TAGS {
            assert!(main_names.insert(main.name));
            assert!(!main.subtags.is_empty());
            let mut subtag_names = HashSet::new();
            for subtag in main.subtags {
                assert!(subtag_names.insert(subtag.name));
                assert!(!subtag.description.trim().is_empty());
            }
        }
    }

    #[test]
    fn syllabus_sections_have_expected_first_class_domains() {
        let gs2 = main_tags_for_section("mains-gs2")
            .unwrap()
            .into_iter()
            .map(|tag| tag.name)
            .collect::<Vec<_>>();
        assert!(gs2.contains(&"International Relations"));
        assert!(gs2.contains(&"Governance"));

        let gs3 = main_tags_for_section("mains-gs3")
            .unwrap()
            .into_iter()
            .map(|tag| tag.name)
            .collect::<Vec<_>>();
        assert!(gs3.contains(&"Internal Security"));
        assert!(gs3.contains(&"Disaster Management"));
    }
}
