export interface BusinessQuestion {
  question: string;
  category: string;
  subcategory: string;
}

// Only questions with truly grounded answers (32 total, 53.3% success rate)
export const businessQuestions: BusinessQuestion[] = [
  // REVENUE & FINANCIAL PERFORMANCE
  {
    category: "Revenue & Financial Performance",
    subcategory: "ARR Analysis",
    question: "What percentage of our ARR is dependent on customers with success scores below 70?" // Q1
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Risk",
    question: "What is the impact on revenue if we lose our top 3 enterprise customers?" // Q3
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Financial Metrics",
    question: "What is the ratio of operational costs to revenue for each product?" // Q23
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Distribution",
    question: "What percentage of our revenue comes from the top 10% of customers?" // Q33
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Analysis",
    question: "What is the average revenue per employee across different departments?" // Q39
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Revenue Type",
    question: "What percentage of revenue is recurring vs one-time?" // Q52
  },

  // CUSTOMER SUCCESS & RETENTION
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Health",
    question: "How many customers have success scores below 60, and what is their combined ARR?" // Q4
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Events",
    question: "What percentage of customers experienced negative events in the last 90 days?" // Q5
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Churn Risk",
    question: "Which customers are at highest risk of churn based on success scores and recent events?" // Q6
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Retention Metrics",
    question: "What is the customer retention rate across different product lines?" // Q10
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Service Impact",
    question: "How many customers would be affected if SpyroCloud experiences an outage?" // Q13
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Regional Analysis",
    question: "Which regions have the highest concentration of at-risk customers?" // Q15
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Product Usage",
    question: "What percentage of our customer base uses multiple products?" // Q16
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Customer Value",
    question: "Which customers have the highest lifetime value?" // Q18
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Acquisition Metrics",
    question: "What is the average customer acquisition cost by product line?" // Q21
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Satisfaction Trends",
    question: "What is the customer satisfaction trend over the past year?" // Q30
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Support Costs",
    question: "What is the cost per customer for each support tier?" // Q35
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Onboarding Success",
    question: "What is the success rate of our customer onboarding process?" // Q37
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Feature Adoption",
    question: "What percentage of features are actively used by more than 50% of customers?" // Q41
  },
  {
    category: "Customer Success & Retention",
    subcategory: "NPS Analysis",
    question: "What percentage of customers are promoters (NPS score 9-10)?" // Q45
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Contract Distribution",
    question: "What is the distribution of contract values across customer segments?" // Q47
  },
  {
    category: "Customer Success & Retention",
    subcategory: "Executive Sponsors",
    question: "What percentage of customers have executive sponsors?" // Q58
  },

  // PRODUCT & FEATURE MANAGEMENT
  {
    category: "Product & Feature Management",
    subcategory: "Feature Performance",
    question: "Which product features have the highest usage but lowest satisfaction scores?" // Q11
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Integrations",
    question: "Which product integrations are most valuable to customers?" // Q38
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Updates",
    question: "Which product updates have had the most positive impact on retention?" // Q46
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Usage Insights",
    question: "What is the relationship between product usage and renewal probability?" // Q56
  },

  // RISK MANAGEMENT
  {
    category: "Risk Management",
    subcategory: "Operational Efficiency",
    question: "Which teams have the highest operational costs relative to their output?" // Q8
  },
  {
    category: "Risk Management",
    subcategory: "Financial Risk",
    question: "How many active risks are unmitigated, and what is their potential financial impact?" // Q9
  },
  {
    category: "Risk Management",
    subcategory: "Team Performance",
    question: "What is the correlation between team size and project completion rates?" // Q19
  },
  {
    category: "Risk Management",
    subcategory: "Pipeline Risk",
    question: "How many high-value opportunities are in the pipeline?" // Q44
  },
  {
    category: "Risk Management",
    subcategory: "Marketing ROI",
    question: "Which marketing channels have the highest ROI?" // Q53
  },

  // STRATEGIC PLANNING
  {
    category: "Strategic Planning",
    subcategory: "Health Metrics",
    question: "What is the average health score by product line?" // Q46 (duplicate removed)
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