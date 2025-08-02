export interface BusinessQuestion {
  question: string;
  category: string;
  subcategory: string;
}

export const businessQuestions: BusinessQuestion[] = [
  // REVENUE & FINANCIAL PERFORMANCE
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk Analysis",
    question: "How much revenue will be at risk if TechCorp misses their SLA next month?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk Analysis",
    question: "What percentage of our ARR is dependent on customers with success scores below 70?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk Analysis",
    question: "Which customers generate 80% of our revenue, and what are their current risk profiles?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk Analysis",
    question: "How much revenue is at risk from customers experiencing negative events in the last quarter?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk Analysis",
    question: "What is the projected revenue impact if we miss our roadmap deadlines for committed features?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Cost & Profitability",
    question: "How much does it cost to run each product across all regions?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Cost & Profitability",
    question: "What is the profitability margin for each product line?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Cost & Profitability",
    question: "How do operational costs impact profitability for our top 10 customers?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Cost & Profitability",
    question: "Which teams have the highest operational costs relative to the revenue they support?"
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Cost & Profitability",
    question: "What is the cost-per-customer for each product, and how does it vary by region?"
  },

  // CUSTOMER SUCCESS & RETENTION
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "What are the top 5 customers by revenue, and what are their current success scores?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "Which customers have declining success scores, and what events are driving the decline?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "How many customers have success scores below 60, and what is their combined ARR?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "What percentage of customers experienced negative events in the last 90 days?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "Which customers are at highest risk of churn based on success scores and recent events?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Commitments & Satisfaction",
    question: "What are the top customer commitments, and what are the current risks to achieving them?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Commitments & Satisfaction",
    question: "Which features were promised to customers, and what is their delivery status?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Commitments & Satisfaction",
    question: "What are the top customer concerns, and what is currently being done to address them?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Commitments & Satisfaction",
    question: "How many customers are waiting for features currently on our roadmap?"
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Commitments & Satisfaction",
    question: "Which customers have unmet SLA commitments in the last quarter?"
  },

  // PRODUCT & FEATURE MANAGEMENT
  {
    category: "Product & Feature Management",
    subcategory: "Product Performance",
    question: "Which products have the highest customer satisfaction scores?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Performance",
    question: "What features drive the most value for our enterprise customers?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Performance",
    question: "How many customers use each product, and what is the average subscription value?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Performance",
    question: "Which products have the most operational issues impacting customer success?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Performance",
    question: "What is the adoption rate of new features released in the last 6 months?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap & Delivery Risk",
    question: "How much future revenue will be at risk if Multi-region deployment misses its deadline by 3 months?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap & Delivery Risk",
    question: "Which roadmap items are critical for customer retention?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap & Delivery Risk",
    question: "What percentage of roadmap items are currently behind schedule?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap & Delivery Risk",
    question: "Which teams are responsible for delayed roadmap items?"
  },
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap & Delivery Risk",
    question: "How many customer commitments depend on roadmap items at risk?"
  },

  // RISK MANAGEMENT
  {
    category: "Risk Management",
    subcategory: "Strategic Risk Assessment",
    question: "What are the top risks related to achieving Market Expansion objective?"
  },
  {
    category: "Risk Management",
    subcategory: "Strategic Risk Assessment",
    question: "Which company objectives have the highest number of associated risks?"
  },
  {
    category: "Risk Management",
    subcategory: "Strategic Risk Assessment",
    question: "What is the potential revenue impact of our top 5 identified risks?"
  },
  {
    category: "Risk Management",
    subcategory: "Strategic Risk Assessment",
    question: "Which risks affect multiple objectives or customer segments?"
  },
  {
    category: "Risk Management",
    subcategory: "Strategic Risk Assessment",
    question: "How many high-severity risks are currently without mitigation strategies?"
  },
  {
    category: "Risk Management",
    subcategory: "Operational Risk",
    question: "Which teams are understaffed relative to their project commitments?"
  },
  {
    category: "Risk Management",
    subcategory: "Operational Risk",
    question: "What operational risks could impact product SLAs?"
  },
  {
    category: "Risk Management",
    subcategory: "Operational Risk",
    question: "Which products have the highest operational risk exposure?"
  },
  {
    category: "Risk Management",
    subcategory: "Operational Risk",
    question: "How do operational risks correlate with customer success scores?"
  },
  {
    category: "Risk Management",
    subcategory: "Operational Risk",
    question: "What percentage of projects are at risk of missing deadlines?"
  },

  // TEAM & RESOURCE MANAGEMENT
  {
    category: "Team & Resource Management",
    subcategory: "Team Performance",
    question: "Which teams support the most revenue-generating products?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Team Performance",
    question: "What is the revenue-per-team-member for each department?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Team Performance",
    question: "Which teams are working on the most critical customer commitments?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Team Performance",
    question: "How are teams allocated across products and projects?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Team Performance",
    question: "Which teams have the highest impact on customer success scores?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Project Delivery",
    question: "Which projects are critical for maintaining current revenue?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Project Delivery",
    question: "What percentage of projects are delivering on schedule?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Project Delivery",
    question: "Which projects have dependencies that could impact multiple products?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Project Delivery",
    question: "How many projects are blocked by operational constraints?"
  },
  {
    category: "Team & Resource Management",
    subcategory: "Project Delivery",
    question: "What is the success rate of projects by team and product area?"
  },

  // STRATEGIC PLANNING
  {
    category: "Strategic Planning",
    subcategory: "Growth & Expansion",
    question: "Which customer segments offer the highest growth potential?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Growth & Expansion",
    question: "What products have the best profitability-to-cost ratio for scaling?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Growth & Expansion",
    question: "Which regions show the most promise for expansion based on current metrics?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Growth & Expansion",
    question: "What features could we develop to increase customer success scores?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Growth & Expansion",
    question: "Which objectives are most critical for achieving our growth targets?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Competitive Positioning",
    question: "How do our SLAs compare to industry standards by product?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Competitive Positioning",
    question: "Which features give us competitive advantage in each market segment?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Competitive Positioning",
    question: "What operational improvements would most impact customer satisfaction?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Competitive Positioning",
    question: "How can we reduce operational costs while maintaining service quality?"
  },
  {
    category: "Strategic Planning",
    subcategory: "Competitive Positioning",
    question: "Which customer segments are we best positioned to serve profitably?"
  }
];

// Group questions by category for easier display
export const questionsByCategory = businessQuestions.reduce((acc, question) => {
  if (!acc[question.category]) {
    acc[question.category] = {};
  }
  if (!acc[question.category][question.subcategory]) {
    acc[question.category][question.subcategory] = [];
  }
  acc[question.category][question.subcategory].push(question.question);
  return acc;
}, {} as Record<string, Record<string, string[]>>);