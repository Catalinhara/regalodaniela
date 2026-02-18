import React from 'react';
import './BirthdayCard.css';

interface BirthdayCardProps {
    onContinue: () => void;
}

export const BirthdayCard: React.FC<BirthdayCardProps> = ({ onContinue }) => {
    return (
        <div className="birthday-container">
            {/* Confetti Animation */}
            <div className="confetti-container">
                {Array.from({ length: 20 }).map((_, i) => (
                    <div key={`confetti-${i}`} className="confetti" />
                ))}
            </div>

            {/* Sparkles */}
            <div className="sparkle-container">
                {Array.from({ length: 8 }).map((_, i) => (
                    <div key={`sparkle-${i}`} className="sparkle">✨</div>
                ))}
            </div>

            {/* Floating Hearts */}
            <div className="hearts-container">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={`heart-${i}`} className="heart">❤️</div>
                ))}
            </div>

            {/* Main Card */}
            <div className="birthday-card">
                <div className="card-ribbon" />

                {/* Balloon Decorations */}
                <div className="balloon-decoration balloon-left">🎈</div>
                <div className="balloon-decoration balloon-right">🎈</div>

                {/* Content */}
                <div className="birthday-emoji">🎉</div>

                <h1 className="birthday-title">¡Feliz Cumpleaños Danielita!</h1>
                <p className="birthday-subtitle">Celebrando tus 33 años ✨</p>

                <div className="birthday-message">
                    <p style={{ margin: 0, position: 'relative', zIndex: 1 }}>
                        En este día tan especial quiero recordarte lo extraordinaria que eres.
                        Iluminas la vida de quienes te rodean, y tu sola presencia hace del mundo
                        un lugar más bonito, más verdadero y mas divertido.
                    </p>
                    <p style={{ margin: '1rem 0 0 0', position: 'relative', zIndex: 1 }}>
                        Que estos 33 años estén llenos de momentos mágicos, sueños cumplidos
                        y sonrisas infinitas. ¡Celebremos juntos este bonito regalo que es tu vida!
                    </p>
                </div>

                <p className="birthday-signature">
                    Espero que este pequeño detalle te sea útil para afrontar y aguantar mejor los desafíos de día a día.
                    Lo hice con todo mi cariño 💕
                </p>

                <button
                    className="birthday-button"
                    onClick={onContinue}
                >
                    Continuar ✨
                </button>
            </div>
        </div>
    );
};
