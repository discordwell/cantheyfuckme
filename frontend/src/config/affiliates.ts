// Affiliate offers configuration
// These are contextual offers shown during document analysis loading

export interface AffiliateOffer {
  id: string
  name: string
  tagline: string
  description: string
  cta: string
  url: string
  logo?: string
  category: string
}

// Map document types to relevant affiliate offers
export const affiliateOffers: Record<string, AffiliateOffer[]> = {
  // Insurance-related documents (COI, insurance_policy)
  insurance: [
    {
      id: 'policygenius',
      name: 'Policygenius',
      tagline: 'Compare insurance quotes in minutes',
      description: 'See if you could save on your insurance. Compare quotes from top carriers.',
      cta: 'Get Free Quotes',
      url: 'https://policygenius.com/?ref=cantheyfuckme',
      category: 'insurance'
    },
    {
      id: 'thezebra',
      name: 'The Zebra',
      tagline: 'Compare car insurance in 5 minutes',
      description: 'The Zebra compares 100+ insurance companies to find you the best rate.',
      cta: 'Compare Rates',
      url: 'https://thezebra.com/?ref=cantheyfuckme',
      category: 'insurance'
    },
    {
      id: 'ethos',
      name: 'Ethos Life',
      tagline: 'Life insurance without the hassle',
      description: 'Get covered in 10 minutes. No medical exams required for most applicants.',
      cta: 'Get a Quote',
      url: 'https://ethos.com/?ref=cantheyfuckme',
      category: 'insurance'
    }
  ],

  // Lease documents
  lease: [
    {
      id: 'zillow',
      name: 'Zillow',
      tagline: 'Find your next place',
      description: 'Looking for a better deal? Browse apartments and rentals in your area.',
      cta: 'Browse Rentals',
      url: 'https://zillow.com/rentals/?ref=cantheyfuckme',
      category: 'rental'
    },
    {
      id: 'apartments',
      name: 'Apartments.com',
      tagline: 'Find the right apartment for you',
      description: 'Millions of apartments. One search. Find deals and move-in specials.',
      cta: 'Search Apartments',
      url: 'https://apartments.com/?ref=cantheyfuckme',
      category: 'rental'
    },
    {
      id: 'lemonade-renters',
      name: 'Lemonade Renters',
      tagline: 'Renters insurance from $5/mo',
      description: 'Get renters insurance in 90 seconds. Instant everything, powered by AI.',
      cta: 'Get Covered',
      url: 'https://lemonade.com/renters/?ref=cantheyfuckme',
      category: 'insurance'
    }
  ],

  // Gym contracts
  gym: [
    {
      id: 'classpass',
      name: 'ClassPass',
      tagline: 'One membership, unlimited options',
      description: 'Access gyms, fitness classes, and wellness experiences near you.',
      cta: 'Try ClassPass Free',
      url: 'https://classpass.com/?ref=cantheyfuckme',
      category: 'fitness'
    },
    {
      id: 'peloton',
      name: 'Peloton App',
      tagline: 'Workout anytime, anywhere',
      description: 'Thousands of classes. No equipment needed for most. Cancel anytime.',
      cta: 'Start Free Trial',
      url: 'https://onepeloton.com/app/?ref=cantheyfuckme',
      category: 'fitness'
    }
  ],

  // Employment contracts
  employment: [
    {
      id: 'legalzoom',
      name: 'LegalZoom',
      tagline: 'Legal help made simple',
      description: 'Need to understand your rights? Get affordable legal advice.',
      cta: 'Talk to a Lawyer',
      url: 'https://legalzoom.com/?ref=cantheyfuckme',
      category: 'legal'
    },
    {
      id: 'rocketlawyer',
      name: 'Rocket Lawyer',
      tagline: 'Legal made simple',
      description: 'Create legal documents, get attorney advice, and protect what matters.',
      cta: 'Get Legal Help',
      url: 'https://rocketlawyer.com/?ref=cantheyfuckme',
      category: 'legal'
    },
    {
      id: 'levels',
      name: 'levels.fyi',
      tagline: 'Know your worth',
      description: 'See what others in your role are making. Negotiate with confidence.',
      cta: 'Check Salaries',
      url: 'https://levels.fyi/?ref=cantheyfuckme',
      category: 'career'
    }
  ],

  // Freelancer contracts
  freelancer: [
    {
      id: 'bonsai',
      name: 'Bonsai',
      tagline: 'Freelance contracts made easy',
      description: 'Create bulletproof contracts, proposals, and invoices in minutes.',
      cta: 'Try Bonsai Free',
      url: 'https://hellobonsai.com/?ref=cantheyfuckme',
      category: 'freelance'
    },
    {
      id: 'rocketlawyer-freelance',
      name: 'Rocket Lawyer',
      tagline: 'Protect your freelance business',
      description: 'Get contract templates, legal advice, and business formation help.',
      cta: 'Get Started',
      url: 'https://rocketlawyer.com/freelance/?ref=cantheyfuckme',
      category: 'legal'
    }
  ],

  // Influencer contracts
  influencer: [
    {
      id: 'klear',
      name: 'Klear',
      tagline: 'Know your worth',
      description: 'Calculate your rates and find brand deals that pay what you deserve.',
      cta: 'Calculate My Rate',
      url: 'https://klear.com/?ref=cantheyfuckme',
      category: 'creator'
    },
    {
      id: 'bonsai-creator',
      name: 'Bonsai for Creators',
      tagline: 'Creator-friendly contracts',
      description: 'Contracts that protect your content and rights. Used by 500K+ creators.',
      cta: 'Get Free Templates',
      url: 'https://hellobonsai.com/creators/?ref=cantheyfuckme',
      category: 'creator'
    }
  ],

  // Timeshare contracts
  timeshare: [
    {
      id: 'timeshare-exit-team',
      name: 'Timeshare Exit',
      tagline: 'Get out of your timeshare',
      description: 'Stuck in a timeshare? Our experts help you exit legally and permanently.',
      cta: 'Get Free Consultation',
      url: 'https://timeshareexit.com/?ref=cantheyfuckme',
      category: 'timeshare'
    },
    {
      id: 'vrbo',
      name: 'VRBO',
      tagline: 'Vacation rentals without commitment',
      description: 'Skip the timeshare trap. Rent vacation homes when YOU want.',
      cta: 'Browse Rentals',
      url: 'https://vrbo.com/?ref=cantheyfuckme',
      category: 'travel'
    }
  ],

  // Auto purchase contracts
  auto: [
    {
      id: 'truecar',
      name: 'TrueCar',
      tagline: 'Know what you should pay',
      description: 'See what others paid for the same car and get upfront pricing before you sign.',
      cta: 'See Pricing',
      url: 'https://truecar.com/?ref=cantheyfuckme',
      category: 'auto'
    },
    {
      id: 'thezebra-auto',
      name: 'The Zebra',
      tagline: 'Compare car insurance in 5 minutes',
      description: 'Just bought a car? Compare 100+ insurers before you overpay on coverage.',
      cta: 'Compare Rates',
      url: 'https://thezebra.com/?ref=cantheyfuckme',
      category: 'insurance'
    }
  ],

  // Home improvement / contractor contracts
  home: [
    {
      id: 'angi',
      name: 'Angi',
      tagline: 'Find pros you can trust',
      description: 'Compare vetted contractors, read real reviews, and get quotes before you commit.',
      cta: 'Find a Pro',
      url: 'https://angi.com/?ref=cantheyfuckme',
      category: 'home'
    },
    {
      id: 'rocketlawyer-home',
      name: 'Rocket Lawyer',
      tagline: 'Protect your project',
      description: 'Review your contractor agreement and get attorney help with liens and disputes.',
      cta: 'Get Legal Help',
      url: 'https://rocketlawyer.com/?ref=cantheyfuckme',
      category: 'legal'
    }
  ],

  // Documents that mostly call for general legal help (e.g. nursing home admission)
  legal: [
    {
      id: 'legalzoom-elder',
      name: 'LegalZoom',
      tagline: 'Legal help made simple',
      description: 'Get affordable attorney advice on admission terms, power of attorney, and your rights.',
      cta: 'Talk to a Lawyer',
      url: 'https://legalzoom.com/?ref=cantheyfuckme',
      category: 'legal'
    },
    {
      id: 'rocketlawyer-legal',
      name: 'Rocket Lawyer',
      tagline: 'Legal made simple',
      description: 'Ask an attorney about clauses you cannot sign away and document what you agreed to.',
      cta: 'Get Legal Help',
      url: 'https://rocketlawyer.com/?ref=cantheyfuckme',
      category: 'legal'
    }
  ],

  // Subscription / SaaS agreements
  subscription: [
    {
      id: 'rocketmoney',
      name: 'Rocket Money',
      tagline: 'Cancel subscriptions in a tap',
      description: 'Find and cancel unwanted subscriptions automatically, and negotiate your bills down.',
      cta: 'Find Subscriptions',
      url: 'https://rocketmoney.com/?ref=cantheyfuckme',
      category: 'finance'
    }
  ],

  // Debt settlement / collection agreements
  debt: [
    {
      id: 'nationaldebtrelief',
      name: 'National Debt Relief',
      tagline: 'Resolve debt for less than you owe',
      description: 'See if you qualify to reduce what you owe with a free, no-obligation evaluation.',
      cta: 'Check Eligibility',
      url: 'https://nationaldebtrelief.com/?ref=cantheyfuckme',
      category: 'finance'
    },
    {
      id: 'nerdwallet-debt',
      name: 'NerdWallet',
      tagline: 'Make smarter money moves',
      description: 'Compare debt payoff options and credit tools, and get personalized recommendations.',
      cta: 'Explore Options',
      url: 'https://nerdwallet.com/?ref=cantheyfuckme',
      category: 'finance'
    }
  ],

  // Default/fallback offers
  default: [
    {
      id: 'legalzoom-default',
      name: 'LegalZoom',
      tagline: 'Legal help made simple',
      description: 'Need legal advice? Get answers from attorneys at affordable prices.',
      cta: 'Talk to a Lawyer',
      url: 'https://legalzoom.com/?ref=cantheyfuckme',
      category: 'legal'
    },
    {
      id: 'nerdwallet',
      name: 'NerdWallet',
      tagline: 'Make smarter money moves',
      description: 'Compare financial products and get personalized recommendations.',
      cta: 'Explore Options',
      url: 'https://nerdwallet.com/?ref=cantheyfuckme',
      category: 'finance'
    }
  ]
}

// Get offers for a specific document type
export function getOffersForDocType(docType: string): AffiliateOffer[] {
  // Map document types to affiliate categories. Every analyzable doc type the
  // SPA can produce (see constants/doc-types.ts ANALYZABLE_DOC_TYPES) maps to a
  // contextual category here; only 'contract'/'unknown' fall through to default.
  const typeMapping: Record<string, string> = {
    coi: 'insurance',
    insurance_policy: 'insurance',
    lease: 'lease',
    gym: 'gym',
    employment: 'employment',
    freelancer: 'freelancer',
    influencer: 'influencer',
    timeshare: 'timeshare',
    auto_purchase: 'auto',
    home_improvement: 'home',
    nursing_home: 'legal',
    subscription: 'subscription',
    debt_settlement: 'debt'
  }

  const category = typeMapping[docType] || 'default'
  return affiliateOffers[category] || affiliateOffers.default
}

// Get a random offer for rotation
export function getRandomOffer(docType: string): AffiliateOffer {
  const offers = getOffersForDocType(docType)
  return offers[Math.floor(Math.random() * offers.length)]
}
