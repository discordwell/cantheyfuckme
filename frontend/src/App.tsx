import { useState, useEffect, useMemo } from 'react'
import './App.css'
import { getOffersForDocType } from './config/affiliates'
import { STRIPE_DONATION_LINK } from './config/stripe'
import { API_BASE } from './services/api'
import { donationTexts } from './constants/donation'
import type {
  ComplianceReport,
  LeaseAnalysisReport,
  GymContractReport,
  EmploymentContractReport,
  FreelancerContractReport,
  InfluencerContractReport,
  TimeshareContractReport,
  InsurancePolicyReport,
  AutoPurchaseReport,
  HomeImprovementReport,
  NursingHomeReport,
  SubscriptionReport,
  DebtSettlementReport,
} from './types'

// Hooks
import { useAuth } from './hooks/useAuth'
import { useDocumentUpload } from './hooks/useDocumentUpload'
import { useAnalyzer } from './hooks/useAnalyzer'
import { useDisclaimer } from './hooks/useDisclaimer'

// Components
import Header from './components/Header'
import InputSection from './components/InputSection'
import Footer from './components/Footer'
import LoadingOverlay from './components/LoadingOverlay'
import DisclaimerModal from './components/modals/DisclaimerModal'
import UnsupportedModal from './components/modals/UnsupportedModal'
import AuthModal from './components/modals/AuthModal'
import HistoryModal from './components/modals/HistoryModal'

// Reports
import COIReport from './components/reports/COIReport'
import LeaseReport from './components/reports/LeaseReport'
import GymReport from './components/reports/GymReport'
import EmploymentReport from './components/reports/EmploymentReport'
import FreelancerReport from './components/reports/FreelancerReport'
import InfluencerReport from './components/reports/InfluencerReport'
import TimeshareReport from './components/reports/TimeshareReport'
import InsurancePolicyReport_ from './components/reports/InsurancePolicyReport'
import AutoPurchaseReport_ from './components/reports/AutoPurchaseReport'
import HomeImprovementReport_ from './components/reports/HomeImprovementReport'
import NursingHomeReport_ from './components/reports/NursingHomeReport'
import SubscriptionReport_ from './components/reports/SubscriptionReport'
import DebtSettlementReport_ from './components/reports/DebtSettlementReport'

function App() {
  const [scanLines] = useState(true)

  // Donation text - randomized on mount
  const [donationText] = useState(() => donationTexts[Math.floor(Math.random() * donationTexts.length)])

  // Affiliate offer rotation. We track only the rotating index; the offer shown
  // is derived below from the index and the offers for the current doc type, so
  // the rotation effect never has to call setState synchronously in its body.
  const [offerIndex, setOfferIndex] = useState(0)

  // Auth hook
  const auth = useAuth()

  // Analyzers (each manages its own report + tab + loading state)
  const coi = useAnalyzer<ComplianceReport>(auth.authToken)
  const lease = useAnalyzer<LeaseAnalysisReport>(auth.authToken)
  const gym = useAnalyzer<GymContractReport>(auth.authToken)
  const employment = useAnalyzer<EmploymentContractReport>(auth.authToken)
  const freelancer = useAnalyzer<FreelancerContractReport>(auth.authToken)
  const influencer = useAnalyzer<InfluencerContractReport>(auth.authToken)
  const timeshare = useAnalyzer<TimeshareContractReport>(auth.authToken)
  const insurancePolicy = useAnalyzer<InsurancePolicyReport>(auth.authToken)
  const autoPurchase = useAnalyzer<AutoPurchaseReport>(auth.authToken)
  const homeImprovement = useAnalyzer<HomeImprovementReport>(auth.authToken)
  const nursingHome = useAnalyzer<NursingHomeReport>(auth.authToken)
  const subscription = useAnalyzer<SubscriptionReport>(auth.authToken)
  const debtSettlement = useAnalyzer<DebtSettlementReport>(auth.authToken)

  const resetAllReports = () => {
    coi.reset()
    lease.reset()
    gym.reset()
    employment.reset()
    freelancer.reset()
    influencer.reset()
    timeshare.reset()
    insurancePolicy.reset()
    autoPurchase.reset()
    homeImprovement.reset()
    nursingHome.reset()
    subscription.reset()
    debtSettlement.reset()
  }

  // Document upload hook
  const upload = useDocumentUpload({ onReportsReset: resetAllReports })

  // Combined loading state
  const anyLoading = coi.loading || lease.loading || gym.loading || employment.loading ||
    freelancer.loading || influencer.loading || timeshare.loading || insurancePolicy.loading ||
    autoPurchase.loading || homeImprovement.loading || nursingHome.loading || subscription.loading || debtSettlement.loading

  // Run the right analyzer based on doc type
  const runAnalysis = async (docTypeStr: string | undefined) => {
    switch (docTypeStr) {
      case 'coi':
        await coi.analyze({
          endpoint: '/api/check-coi-compliance',
          buildBody: () => ({ coi_text: upload.docText, project_type: upload.projectType, state: upload.selectedState || null }),
          errorMessage: 'Compliance check failed.',
        })
        break
      case 'lease':
        await lease.analyze({
          endpoint: '/api/analyze-lease',
          buildBody: () => ({ lease_text: upload.docText, state: upload.selectedState || null, lease_type: 'commercial' }),
          errorMessage: 'Lease analysis failed.',
        })
        break
      case 'gym':
        await gym.analyze({
          endpoint: '/api/analyze-gym',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Gym contract analysis failed.',
        })
        break
      case 'employment':
        await employment.analyze({
          endpoint: '/api/analyze-employment',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Employment contract analysis failed.',
        })
        break
      case 'freelancer':
        await freelancer.analyze({
          endpoint: '/api/analyze-freelancer',
          buildBody: () => ({ contract_text: upload.docText }),
          errorMessage: 'Freelancer contract analysis failed.',
        })
        break
      case 'influencer':
        await influencer.analyze({
          endpoint: '/api/analyze-influencer',
          buildBody: () => ({ contract_text: upload.docText }),
          errorMessage: 'Influencer contract analysis failed.',
        })
        break
      case 'timeshare':
        await timeshare.analyze({
          endpoint: '/api/analyze-timeshare',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Timeshare contract analysis failed.',
        })
        break
      case 'insurance_policy':
        await insurancePolicy.analyze({
          endpoint: '/api/analyze-insurance-policy',
          buildBody: () => ({ policy_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Insurance policy analysis failed.',
        })
        break
      case 'auto_purchase':
        await autoPurchase.analyze({
          endpoint: '/api/analyze-auto-purchase',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Auto purchase analysis failed.',
        })
        break
      case 'home_improvement':
        await homeImprovement.analyze({
          endpoint: '/api/analyze-home-improvement',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Home improvement analysis failed.',
        })
        break
      case 'nursing_home':
        await nursingHome.analyze({
          endpoint: '/api/analyze-nursing-home',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Nursing home analysis failed.',
        })
        break
      case 'subscription':
        await subscription.analyze({
          endpoint: '/api/analyze-subscription',
          buildBody: () => ({ contract_text: upload.docText }),
          errorMessage: 'Subscription analysis failed.',
        })
        break
      case 'debt_settlement':
        await debtSettlement.analyze({
          endpoint: '/api/analyze-debt-settlement',
          buildBody: () => ({ contract_text: upload.docText, state: upload.selectedState || null }),
          errorMessage: 'Debt settlement analysis failed.',
        })
        break
    }
  }

  // Disclaimer hook
  const disclaimer = useDisclaimer({ runAnalysis })

  // Handle analyze button
  const handleAnalyze = async () => {
    if (!upload.docText.trim()) return

    // Start the offer rotation from the first offer for this run.
    setOfferIndex(0)

    // If no classification yet, classify first
    let currentDocType = upload.docType
    if (!currentDocType) {
      const classification = await upload.classifyDocument(upload.docText)
      upload.handleClassification(classification)
      if (!classification?.supported) return
      upload.setDocType(classification)
      currentDocType = classification
    }

    // If disclaimer not yet accepted, show the modal
    if (!disclaimer.disclaimerAccepted) {
      const docTypeStr = currentDocType?.document_type
      if (docTypeStr && ['coi', 'lease', 'gym', 'employment', 'freelancer', 'influencer', 'timeshare', 'insurance_policy', 'auto_purchase', 'home_improvement', 'nursing_home', 'subscription', 'debt_settlement'].includes(docTypeStr)) {
        disclaimer.setPendingAnalysis(docTypeStr as 'coi' | 'lease' | 'gym' | 'employment' | 'freelancer' | 'influencer' | 'timeshare' | 'insurance_policy' | 'auto_purchase' | 'home_improvement' | 'nursing_home' | 'subscription' | 'debt_settlement')
      }
      disclaimer.setShowDisclaimerModal(true)
      disclaimer.setDisclaimerInput('')
      return
    }

    // Route to appropriate analyzer
    await runAnalysis(currentDocType?.document_type)
  }

  // Waitlist submit
  const handleWaitlistSubmit = async () => {
    try {
      await fetch(`${API_BASE}/api/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: upload.waitlistEmail,
          document_type: upload.unsupportedType,
          document_text: upload.docText
        })
      })
    } catch (err) {
      console.error('Waitlist signup failed:', err)
    }
    upload.setEmailSubmitted(true)
  }

  // Reset all state
  const resetAll = () => {
    upload.setUploadedFileName(null)
    upload.setDocText('')
    upload.setDocType(null)
    upload.setOcrNotice(null)
    upload.setShowUnsupportedModal(false)
    upload.setWaitlistEmail('')
    upload.setEmailSubmitted(false)
    resetAllReports()
    setOfferIndex(0)
    disclaimer.setDisclaimerAccepted(false)
    disclaimer.setDisclaimerInput('')
    disclaimer.setPendingAnalysis(null)
  }

  // Offers relevant to the classified document. Keyed on the document-type
  // string the offers actually depend on (not the ClassifyResult identity), so
  // it recomputes exactly when the type changes. getOffersForDocType returns a
  // fresh array on every call, so memoizing also keeps the timer effect stable.
  const docTypeStr = upload.docType?.document_type
  const activeOffers = useMemo(
    () => (docTypeStr ? getOffersForDocType(docTypeStr) : []),
    [docTypeStr]
  )

  // While an analysis is running, advance the offer index every 5s. The effect
  // owns only the timer; setState happens inside the interval callback (async),
  // not synchronously in the effect body, so there are no cascading renders.
  useEffect(() => {
    if (!anyLoading || activeOffers.length === 0) return

    const interval = setInterval(() => {
      setOfferIndex(prev => (prev + 1) % activeOffers.length)
    }, 5000)

    return () => clearInterval(interval)
  }, [anyLoading, activeOffers])

  // The offer to show is derived, not stored: null unless we're loading and have
  // offers, otherwise the current index (mod length, so it stays in bounds even
  // if the offer set shrank since the index last advanced).
  const currentOffer =
    anyLoading && activeOffers.length > 0
      ? activeOffers[offerIndex % activeOffers.length]
      : null

  // Button text helper
  const getAnalyzeButtonText = () => {
    if (anyLoading) return '[ ANALYZING... ]'
    if (upload.classifying) return '[ READING... ]'
    if (upload.ocrLoading) return '[ EXTRACTING... ]'
    return '> CAN THEY FUCK ME?'
  }

  return (
    <div className={`app ${scanLines ? 'scanlines' : ''}`}>
      <Header
        isLoggedIn={auth.isLoggedIn}
        userEmail={auth.userEmail}
        openHistoryModal={auth.openHistoryModal}
        handleLogout={auth.handleLogout}
        setAuthMode={auth.setAuthMode}
        setShowAuthModal={auth.setShowAuthModal}
      />

      <main className="main">
        <InputSection
          getRootProps={upload.getRootProps}
          getInputProps={upload.getInputProps}
          isDragActive={upload.isDragActive}
          ocrLoading={upload.ocrLoading}
          classifying={upload.classifying}
          loading={anyLoading}
          uploadedFileName={upload.uploadedFileName}
          ocrNotice={upload.ocrNotice}
          docType={upload.docType}
          docText={upload.docText}
          projectType={upload.projectType}
          selectedState={upload.selectedState}
          setDocText={upload.setDocText}
          setDocType={upload.setDocType}
          setOcrNotice={upload.setOcrNotice}
          setProjectType={upload.setProjectType}
          setSelectedState={upload.setSelectedState}
          resetAll={resetAll}
          handleAnalyze={handleAnalyze}
          getAnalyzeButtonText={getAnalyzeButtonText}
        />

        {coi.report && <COIReport report={coi.report} tab={coi.tab} setTab={coi.setTab} />}
        {lease.report && <LeaseReport report={lease.report} tab={lease.tab} setTab={lease.setTab} />}
        {gym.report && <GymReport report={gym.report} tab={gym.tab} setTab={gym.setTab} />}
        {employment.report && <EmploymentReport report={employment.report} tab={employment.tab} setTab={employment.setTab} />}
        {freelancer.report && <FreelancerReport report={freelancer.report} tab={freelancer.tab} setTab={freelancer.setTab} />}
        {influencer.report && <InfluencerReport report={influencer.report} tab={influencer.tab} setTab={influencer.setTab} />}
        {timeshare.report && <TimeshareReport report={timeshare.report} tab={timeshare.tab} setTab={timeshare.setTab} />}
        {insurancePolicy.report && <InsurancePolicyReport_ report={insurancePolicy.report} tab={insurancePolicy.tab} setTab={insurancePolicy.setTab} />}
        {autoPurchase.report && <AutoPurchaseReport_ report={autoPurchase.report} tab={autoPurchase.tab} setTab={autoPurchase.setTab} />}
        {homeImprovement.report && <HomeImprovementReport_ report={homeImprovement.report} tab={homeImprovement.tab} setTab={homeImprovement.setTab} />}
        {nursingHome.report && <NursingHomeReport_ report={nursingHome.report} tab={nursingHome.tab} setTab={nursingHome.setTab} />}
        {subscription.report && <SubscriptionReport_ report={subscription.report} tab={subscription.tab} setTab={subscription.setTab} />}
        {debtSettlement.report && <DebtSettlementReport_ report={debtSettlement.report} tab={debtSettlement.tab} setTab={debtSettlement.setTab} />}
      </main>

      <DisclaimerModal
        show={disclaimer.showDisclaimerModal}
        disclaimerInput={disclaimer.disclaimerInput}
        onInputChange={disclaimer.setDisclaimerInput}
        onSubmit={disclaimer.handleDisclaimerSubmit}
        onCancel={disclaimer.handleDisclaimerCancel}
      />

      <UnsupportedModal
        show={upload.showUnsupportedModal}
        unsupportedType={upload.unsupportedType}
        waitlistEmail={upload.waitlistEmail}
        emailSubmitted={upload.emailSubmitted}
        onEmailChange={upload.setWaitlistEmail}
        onSubmit={handleWaitlistSubmit}
        onClose={() => upload.setShowUnsupportedModal(false)}
        onReset={resetAll}
      />

      <LoadingOverlay loading={anyLoading} currentOffer={currentOffer} />

      <AuthModal
        show={auth.showAuthModal}
        authMode={auth.authMode}
        authEmail={auth.authEmail}
        authPassword={auth.authPassword}
        authError={auth.authError}
        authLoading={auth.authLoading}
        onEmailChange={auth.setAuthEmail}
        onPasswordChange={auth.setAuthPassword}
        onLogin={auth.handleLogin}
        onSignup={auth.handleSignup}
        onClose={() => auth.setShowAuthModal(false)}
        onSwitchMode={auth.setAuthMode}
      />

      <HistoryModal
        show={auth.showHistoryModal}
        historyLoading={auth.historyLoading}
        userHistory={auth.userHistory}
        onClose={() => auth.setShowHistoryModal(false)}
      />

      <Footer donationText={donationText} STRIPE_DONATION_LINK={STRIPE_DONATION_LINK} />
    </div>
  )
}

export default App
