import React, { useState } from 'react';
import './LearningFlowsHub.css';

// Import all flows
import { DailyHand } from './DailyHand';
import { OpeningLead } from './OpeningLead';
import { GuessPartner } from './GuessPartner';
import { PostHandDebrief } from './PostHandDebrief';
import { QuickCount } from './QuickCount';
import { BiddingReplay } from './BiddingReplay';
import { DefensiveSignal } from './DefensiveSignal';
import { CriticalTrick } from './CriticalTrick';
import { ConventionSpotlight } from './ConventionSpotlight';
import { TrainingDashboard } from './TrainingDashboard';

const FLOWS = [
  { id: 'dashboard', name: 'Training Dashboard', icon: '📊', description: 'View your progress and stats' },
  { id: 'daily', name: 'Daily Hand', icon: '📅', description: 'One hand per day challenge' },
  { id: 'lead', name: 'Opening Lead', icon: '🎯', description: 'Practice opening leads' },
  { id: 'guess', name: 'Guess Partner', icon: '🤔', description: 'Estimate partner\'s hand' },
  { id: 'debrief', name: 'Post-Hand Debrief', icon: '📝', description: 'Review completed hands' },
  { id: 'count', name: 'Quick Count', icon: '⚡', description: 'Speed point counting drill' },
  { id: 'replay', name: 'Bidding Replay', icon: '🔄', description: 'Spaced repetition practice' },
  { id: 'signal', name: 'Defensive Signals', icon: '👆', description: 'Learn defensive signals' },
  { id: 'critical', name: 'Critical Trick', icon: '🎲', description: 'Declarer play problems' },
  { id: 'convention', name: 'Convention Spotlight', icon: '📚', description: 'Learn and drill conventions' },
];

/**
 * LearningFlowsHub - Development hub for accessing all learning flows
 * Only visible on localhost
 */
function LearningFlowsHub({ onClose }) {
  const [activeFlow, setActiveFlow] = useState(null);

  const handleFlowComplete = (result) => {
    console.log('Flow completed:', result);
    setActiveFlow(null);
  };

  const handleFlowClose = () => {
    setActiveFlow(null);
  };

  const handleStartSuggested = (flowType, categories) => {
    console.log('Starting suggested flow:', flowType, categories);
    setActiveFlow(flowType);
  };

  // Render active flow - wrapped in container with fixed positioning
  if (activeFlow) {
    const flowProps = {
      onComplete: handleFlowComplete,
      onClose: handleFlowClose,
    };

    let flowComponent = null;
    switch (activeFlow) {
      case 'dashboard':
        flowComponent = <TrainingDashboard {...flowProps} onStartSuggested={handleStartSuggested} />;
        break;
      case 'daily':
        flowComponent = <DailyHand {...flowProps} />;
        break;
      case 'lead':
        flowComponent = <OpeningLead {...flowProps} />;
        break;
      case 'guess':
        flowComponent = <GuessPartner {...flowProps} />;
        break;
      case 'debrief':
        flowComponent = <PostHandDebrief {...flowProps} />;
        break;
      case 'count':
        flowComponent = <QuickCount {...flowProps} />;
        break;
      case 'replay':
        flowComponent = <BiddingReplay {...flowProps} />;
        break;
      case 'signal':
        flowComponent = <DefensiveSignal {...flowProps} />;
        break;
      case 'critical':
        flowComponent = <CriticalTrick {...flowProps} />;
        break;
      case 'convention':
        flowComponent = <ConventionSpotlight {...flowProps} />;
        break;
      default:
        break;
    }

    // Wrap in fixed container to ensure proper z-index layering
    return (
      <div className="learning-flows-hub flow-active">
        {flowComponent}
      </div>
    );
  }

  // Render flow selector
  return (
    <div className="learning-flows-hub">
      <div className="hub-header">
        <h1>Learning Flows Lab</h1>
        <p className="hub-subtitle">Development preview — localhost only</p>
        <button className="hub-close-btn" onClick={onClose}>
          ✕
        </button>
      </div>

      <div className="hub-grid">
        {FLOWS.map((flow) => (
          <button
            key={flow.id}
            className="hub-flow-card"
            onClick={() => setActiveFlow(flow.id)}
          >
            <span className="flow-icon">{flow.icon}</span>
            <span className="flow-name">{flow.name}</span>
            <span className="flow-description">{flow.description}</span>
          </button>
        ))}
      </div>

      <div className="hub-footer">
        <p>These flows use mock data. Connect to backend for full functionality.</p>
      </div>
    </div>
  );
}

export default LearningFlowsHub;
