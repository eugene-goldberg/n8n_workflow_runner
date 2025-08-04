export interface BusinessQuestion {
  question: string;
  category: string;
  subcategory: string;
}

// Only questions with grounded answers (32 total, 53.3% success rate)
export const businessQuestions: BusinessQuestion[] = [
  // REVENUE & FINANCIAL PERFORMANCE
  {
    category: "Revenue & Financial Performance",
    subcategory: "Financial Metrics",
    question: "What is our total ARR and how is it distributed across customer segments?" // Q1
  },
  {
    category: "Revenue & Financial Performance", 
    subcategory: "Customer Risk",
    question: "Which customers have success scores below 50?" // Q2
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Customer Health",
    question: "What is the distribution of customer health scores?" // Q3
  },
  {
    category: "Revenue & Financial Performance",
    subcategory: "Churn Risk",
    question: "How many customers are at risk of churning?" // Q4
  },

  // RISK MANAGEMENT
  {
    category: "Risk Management",
    subcategory: "Financial Impact",
    question: "How many active risks are unmitigated and what is their financial impact?" // Q8
  },
  {
    category: "Risk Management",
    subcategory: "Customer Trends",
    question: "Which customers have declining success scores?" // Q9
  },
  {
    category: "Risk Management",
    subcategory: "Revenue Analysis",
    question: "What is the average contract value by customer segment?" // Q10
  },
  {
    category: "Risk Management",
    subcategory: "Churn Analysis",
    question: "What percentage of customers are at risk of churn based on multiple factors?" // Q12
  },
  {
    category: "Risk Management",
    subcategory: "Risk Categories",
    question: "What are the most common risk categories?" // Q27
  },
  {
    category: "Risk Management",
    subcategory: "Critical Risks",
    question: "What are the most critical unmitigated risks by impact?" // Q40
  },
  {
    category: "Risk Management",
    subcategory: "High-Value Risk",
    question: "How many high-value customers are at risk?" // Q45
  },
  {
    category: "Risk Management",
    subcategory: "Mitigation Plans",
    question: "What percentage of risks have approved mitigation plans?" // Q49
  },

  // CUSTOMER ANALYTICS
  {
    category: "Customer Analytics",
    subcategory: "Revenue Distribution",
    question: "What is the distribution of customers by revenue tier?" // Q14
  },
  {
    category: "Customer Analytics",
    subcategory: "Health Scores",
    question: "What is the health score distribution across all customers?" // Q18
  },
  {
    category: "Customer Analytics",
    subcategory: "Segment Analysis",
    question: "Which customer segments generate the most ARR?" // Q21
  },
  {
    category: "Customer Analytics",
    subcategory: "Product Adoption",
    question: "How does product adoption vary by customer size?" // Q26
  },
  {
    category: "Customer Analytics",
    subcategory: "Success Scores",
    question: "What is the success score trend over the past quarters?" // Q30
  },
  {
    category: "Customer Analytics",
    subcategory: "Low-Score Analysis",
    question: "How many customers have success scores below 60?" // Q39
  },
  {
    category: "Customer Analytics",
    subcategory: "Version Adoption",
    question: "What percentage of customers are on the latest product version?" // Q43
  },
  {
    category: "Customer Analytics",
    subcategory: "Satisfaction Correlation",
    question: "How does customer satisfaction correlate with product adoption?" // Q51
  },
  {
    category: "Customer Analytics",
    subcategory: "Executive Sponsors",
    question: "What percentage of customers have executive sponsors?" // Q58
  },

  // PRODUCT & FEATURE MANAGEMENT
  {
    category: "Product & Feature Management",
    subcategory: "Roadmap Status",
    question: "What percentage of roadmap items are delayed?" // Q32
  },
  {
    category: "Product & Feature Management",
    subcategory: "Feature Adoption",
    question: "What is the adoption rate of features released in the last quarter?" // Q34
  },
  {
    category: "Product & Feature Management",
    subcategory: "Product Revenue",
    question: "Which products contribute most to recurring revenue?" // Q38
  },
  {
    category: "Product & Feature Management",
    subcategory: "Health by Product",
    question: "What is the average health score by product line?" // Q46
  },
  {
    category: "Product & Feature Management",
    subcategory: "Support Burden",
    question: "Which products have the highest support burden?" // Q59
  },

  // FINANCIAL ANALYSIS
  {
    category: "Financial Analysis",
    subcategory: "Revenue Type",
    question: "What percentage of revenue is recurring vs one-time?" // Q52
  },
  {
    category: "Financial Analysis",
    subcategory: "Marketing ROI",
    question: "Which marketing channels have the highest ROI?" // Q53
  },
  {
    category: "Financial Analysis",
    subcategory: "Seasonality",
    question: "What is the impact of seasonality on revenue projections?" // Q55
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