/**
 * CriticalTrick.logic.js
 * Plan evaluation and flow result generation for Critical Trick Flow
 */

import { generateHandId } from '../../types/flow-types';

/**
 * Evaluate a plan selection against the problem
 * @param {string} selectedPlanId - ID of the plan the user selected
 * @param {Object} problem - The critical trick problem
 * @returns {Object} Evaluation result
 */
export function evaluatePlan(selectedPlanId, problem) {
  const selectedPlan = problem.plans.find(p => p.id === selectedPlanId);
  const correctPlan = problem.plans.find(p => p.isCorrect);

  if (!selectedPlan) {
    return {
      isCorrect: false,
      selectedPlan: null,
      correctPlan,
      explanation: 'No plan selected',
      technique: problem.technique
    };
  }

  return {
    isCorrect: selectedPlan.isCorrect,
    selectedPlan,
    correctPlan,
    explanation: selectedPlan.isCorrect ? selectedPlan.explanation : correctPlan.explanation,
    technique: problem.technique,
    selectedExplanation: selectedPlan.explanation
  };
}

/**
 * Get the correct plan from a problem
 * @param {Object} problem - The critical trick problem
 * @returns {Object|null} The correct plan or null
 */
export function getCorrectPlan(problem) {
  return problem.plans.find(p => p.isCorrect) || null;
}

/**
 * Calculate contract details from contract string
 * @param {string} contract - Contract string like "4S", "3NT"
 * @returns {Object} Parsed contract details
 */
export function parseContract(contract) {
  const match = contract.match(/^(\d)(S|H|D|C|NT)$/i);
  if (!match) {
    return { level: 0, strain: '', tricksNeeded: 0 };
  }

  const level = parseInt(match[1], 10);
  const strain = match[2].toUpperCase();
  const tricksNeeded = level + 6;

  const suitSymbols = {
    'S': '\u2660', // spades
    'H': '\u2665', // hearts
    'D': '\u2666', // diamonds
    'C': '\u2663', // clubs
    'NT': 'NT'
  };

  return {
    level,
    strain,
    strainSymbol: suitSymbols[strain] || strain,
    tricksNeeded,
    displayContract: `${level}${suitSymbols[strain] || strain}`
  };
}

/**
 * Generate a FlowResult from the evaluation
 * @param {Object} problem - The critical trick problem
 * @param {Object} evaluation - Result from evaluatePlan
 * @param {number} timeSpent - Milliseconds spent on the problem
 * @returns {Object} FlowResult object
 */
export function generateFlowResult(problem, evaluation, timeSpent = 0) {
  const handId = generateHandId();

  return {
    flowType: 'critical',
    handId,
    timestamp: new Date().toISOString(),
    decisions: [
      {
        decisionId: 'plan-choice',
        category: 'Declarer Play',
        playerAnswer: evaluation.selectedPlan?.label || 'None',
        correctAnswer: evaluation.correctPlan?.label || 'Unknown',
        isCorrect: evaluation.isCorrect,
        explanation: evaluation.explanation,
        conventionTag: problem.technique
      }
    ],
    overallScore: evaluation.isCorrect ? 100 : 0,
    timeSpent,
    conventionTags: [problem.technique]
  };
}

/**
 * Get difficulty rating based on technique
 * @param {string} technique - The technique being tested
 * @returns {'beginner' | 'intermediate' | 'advanced'}
 */
export function getDifficultyRating(technique) {
  const difficultyMap = {
    'Finesse vs Drop': 'intermediate',
    'Hold-up Play': 'beginner',
    'Trump Management': 'intermediate',
    'Endplay': 'advanced',
    'Counting': 'advanced'
  };

  return difficultyMap[technique] || 'intermediate';
}

/**
 * Format situation text with colorized suit symbols
 * @param {string} text - Situation description text
 * @returns {string} Text with suit symbols (caller handles JSX colorization)
 */
export function formatSituationText(text) {
  // Replace text representations with symbols
  return text
    .replace(/\bspades?\b/gi, '\u2660')
    .replace(/\bhearts?\b/gi, '\u2665')
    .replace(/\bdiamonds?\b/gi, '\u2666')
    .replace(/\bclubs?\b/gi, '\u2663');
}

/**
 * Get technique description for learning panel
 * @param {string} technique - The technique name
 * @returns {string} Brief description
 */
export function getTechniqueDescription(technique) {
  const descriptions = {
    'Finesse vs Drop': 'Deciding between finessing for a missing honor or playing for it to drop based on probability and inferences.',
    'Hold-up Play': 'Ducking early rounds to exhaust one opponent of a suit, breaking their communication.',
    'Trump Management': 'Deciding when to draw trumps vs. using them for ruffing or other purposes.',
    'Endplay': 'Stripping opponents of safe exit cards, then throwing them in to make a losing lead.',
    'Counting': 'Using the bidding and play to deduce the distribution and locate key cards.'
  };

  return descriptions[technique] || 'A key declarer play technique.';
}

export default {
  evaluatePlan,
  getCorrectPlan,
  parseContract,
  generateFlowResult,
  getDifficultyRating,
  formatSituationText,
  getTechniqueDescription
};
