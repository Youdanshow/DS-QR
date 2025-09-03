import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { useAuth } from '../contexts/AuthContext';
import { Chrome, Shield, Zap } from 'lucide-react';

const AuthModal = ({ isOpen, onClose }) => {
  const { loginWithGoogle } = useAuth();

  const handleGoogleLogin = () => {
    loginWithGoogle();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-xl">
            Se connecter
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Google Login Button */}
          <Button 
            onClick={handleGoogleLogin}
            className="w-full h-12 text-base bg-white hover:bg-gray-50 text-gray-900 border border-gray-300 shadow-sm"
            size="lg"
          >
            <Chrome className="h-5 w-5 mr-3 text-red-500" />
            Continuer avec Google
          </Button>
          
          {/* Benefits */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-medium text-center text-gray-900">
              Avantages de la connexion :
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-blue-100 p-2">
                  <Zap className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium text-sm">5 QR codes au lieu de 3</p>
                  <p className="text-xs text-gray-600">Limite augmentée pour les utilisateurs connectés</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-green-100 p-2">
                  <Shield className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-sm">Historique sauvegardé</p>
                  <p className="text-xs text-gray-600">Accédez à vos QR codes depuis n'importe où</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Limits Info */}
          <div className="text-center text-sm text-gray-500 p-3 bg-gray-50 rounded-lg">
            <p><strong>Limites:</strong> Invité: 3 QR codes | Connecté: 5 QR codes | Premium: Illimité</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default AuthModal;