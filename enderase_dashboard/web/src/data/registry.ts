// Enderase Youth Association — registry data story dataset (illustrative).

export const registry = {
  registeredYouth: 52487,
  beneficiaries: 18342,
  groups: 1264,
  programs: 47,
  organizations: 312,
  regions: 11,
  trainings: 128,
  growthYoY: 34,
};

export const demographics = {
  female: 27890,
  male: 24597,
  ageBands: [
    { band: "15–18", value: 12480 },
    { band: "19–22", value: 18960 },
    { band: "23–26", value: 13540 },
    { band: "27–30", value: 7507 },
  ],
};

// Membership pipeline
export const pipeline = [
  { stage: "Registration", value: 52487 },
  { stage: "Verification", value: 41230 },
  { stage: "Member", value: 33890 },
  { stage: "Beneficiary", value: 18342 },
  { stage: "Leadership", value: 3120 },
];

// Ethiopia regions with approximate positions on a stylized map (viewBox 0..100)
export const regions = [
  { id: "tigray", name: "Tigray", youth: 4120, beneficiaries: 1450, groups: 96, x: 60, y: 14 },
  { id: "amhara", name: "Amhara", youth: 9840, beneficiaries: 3620, groups: 248, x: 46, y: 30 },
  { id: "afar", name: "Afar", youth: 2110, beneficiaries: 640, groups: 52, x: 70, y: 30 },
  { id: "benishangul", name: "Benishangul", youth: 1580, beneficiaries: 430, groups: 38, x: 26, y: 40 },
  { id: "addis", name: "Addis Ababa", youth: 11230, beneficiaries: 4980, groups: 312, x: 52, y: 50 },
  { id: "dire", name: "Dire Dawa", youth: 2360, beneficiaries: 910, groups: 44, x: 74, y: 46 },
  { id: "harari", name: "Harari", youth: 1180, beneficiaries: 380, groups: 22, x: 76, y: 52 },
  { id: "gambela", name: "Gambela", youth: 1320, beneficiaries: 360, groups: 30, x: 18, y: 58 },
  { id: "oromia", name: "Oromia", youth: 10980, beneficiaries: 3980, groups: 286, x: 48, y: 62 },
  { id: "sidama", name: "Sidama", youth: 3210, beneficiaries: 1120, groups: 68, x: 46, y: 74 },
  { id: "somali", name: "Somali", youth: 4557, beneficiaries: 472, groups: 68, x: 80, y: 66 },
];

export const skills = [
  { name: "Digital Literacy", value: 8940 },
  { name: "Agribusiness", value: 7210 },
  { name: "Tailoring", value: 5120 },
  { name: "Coding", value: 4680 },
  { name: "Handicraft", value: 4020 },
  { name: "Hospitality", value: 3560 },
  { name: "Leadership", value: 3120 },
  { name: "Finance", value: 2890 },
  { name: "Health", value: 2340 },
  { name: "Media", value: 1980 },
];

export const training = [
  { name: "Completed", value: 62 },
  { name: "In Progress", value: 24 },
  { name: "Enrolled", value: 14 },
];

export const trainingWheels = [
  { label: "Vocational", value: 78 },
  { label: "Digital", value: 64 },
  { label: "Business", value: 52 },
  { label: "Civic", value: 41 },
];

export const entrepreneurship = [
  { name: "Startups", value: 640 },
  { name: "Cooperatives", value: 420 },
  { name: "Micro-loans", value: 1180 },
  { name: "Markets", value: 96 },
  { name: "Mentors", value: 210 },
];

export const treemap = [
  { name: "Agriculture", size: 7210 },
  { name: "Technology", size: 4680 },
  { name: "Textiles", size: 5120 },
  { name: "Crafts", size: 4020 },
  { name: "Services", size: 3560 },
  { name: "Creative", size: 1980 },
];

export const growth = [
  { year: "2019", youth: 4200, beneficiaries: 900 },
  { year: "2020", youth: 9800, beneficiaries: 2600 },
  { year: "2021", youth: 18400, beneficiaries: 6100 },
  { year: "2022", youth: 29600, beneficiaries: 10200 },
  { year: "2023", youth: 41200, beneficiaries: 14800 },
  { year: "2024", youth: 52487, beneficiaries: 18342 },
];

export const timeline = [
  { year: "2019", title: "Founded in Addis Ababa", text: "Enderase begins with 12 community groups." },
  { year: "2020", title: "Regional Expansion", text: "Registry reaches 6 regions during nationwide drive." },
  { year: "2021", title: "Digital Registry Launch", text: "Youth onboarded through a unified data platform." },
  { year: "2022", title: "Skills at Scale", text: "Vocational programs cross 20,000 enrollments." },
  { year: "2023", title: "Entrepreneurship Fund", text: "Micro-loans empower 1,000+ young founders." },
  { year: "2024", title: "A National Movement", text: "52,487 youth registered across all 11 regions." },
];

export const quotes = [
  { text: "Enderase gave me the skills to open my own tailoring shop.", name: "Marta, 24", region: "Amhara" },
  { text: "I found a community of young leaders who believe in the same future.", name: "Dawit, 21", region: "Addis Ababa" },
  { text: "From a registered member to running a cooperative of 15 people.", name: "Hanan, 26", region: "Oromia" },
];

export const organizations = [
  { name: "Selam Tech Hub", type: "Technology", members: 420, tone: "gold" },
  { name: "Green Roots Coop", type: "Agriculture", members: 680, tone: "brown" },
  { name: "Weave Collective", type: "Textiles", members: 310, tone: "coffee" },
  { name: "Addis Makers", type: "Crafts", members: 240, tone: "gold" },
  { name: "Youth Voices Media", type: "Creative", members: 180, tone: "brown" },
  { name: "Habesha Hospitality", type: "Services", members: 350, tone: "coffee" },
  { name: "Fintech for All", type: "Finance", members: 150, tone: "gold" },
  { name: "Care Network", type: "Health", members: 260, tone: "brown" },
];

export const sunburst = [
  { region: "Amhara", zones: ["Gondar", "Bahir Dar", "Dessie"] },
  { region: "Oromia", zones: ["Adama", "Jimma", "Bishoftu"] },
  { region: "Addis Ababa", zones: ["Bole", "Kirkos", "Yeka"] },
];
