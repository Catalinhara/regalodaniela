import React from 'react';
import { Insight } from '../api/client';
import './InsightCard.css';

interface InsightCardProps {
    insight: Insight;
}

export const InsightCard: React.FC<InsightCardProps> = ({ insight }) => {
    return (
        <div className="insight-card-subtle">
            <div className="insight-card-inner">
                <div className="insight-main-content">
                    <div className="observation-section">
                        <div className="quote-mark">“</div>
                        <p className="observation-text-subtle">{insight.observation}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
