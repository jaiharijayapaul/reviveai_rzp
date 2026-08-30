import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Shield, CheckCircle2, Bot } from 'lucide-react';
import { useToast } from '../components/ui/use-toast';

interface Policy {
  max_automated_amount: number;
  max_recovery_attempts: number;
  allowed_actions: string;
  high_risk_requires_approval: boolean;
  approval_threshold: number;
}

export default function PolicySettings() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAgentMessage, setLastAgentMessage] = useState("");
  const { toast } = useToast();

  const fetchPolicy = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/policy/");
      const data = await res.json();
      setPolicy(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    setLastAgentMessage("");
    try {
      const res = await fetch("http://localhost:8000/api/policy/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt }),
      });
      const data = await res.json();
      if (data.success) {
        setPolicy(data.policy);
        setLastAgentMessage(data.agent_message);
        setPrompt("");
        toast({
          title: "Policy Updated",
          description: "ReviveAI Co-Pilot successfully updated your rules.",
        });
      } else {
        toast({ title: "Update Failed", description: data.error?.message, variant: "destructive" });
      }
    } catch (e) {
      console.error(e);
      toast({ title: "Error", description: "Could not connect to Co-Pilot.", variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Policy Settings</h1>
        <p className="text-gray-400 mt-2">Manage your AI recovery rules with the ReviveAI Co-Pilot.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Co-Pilot Chat */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bot className="h-6 w-6 text-emerald-400" />
              ReviveAI Co-Pilot
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-300 text-sm">
              Use natural language to configure your recovery policies. For example, try saying: <i>"We are having a Diwali flash sale. Increase the automated recovery limit to ₹25,000."</i>
            </p>
            
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask Co-Pilot to change a rule..."
                className="w-full min-h-[120px] bg-gray-900 border border-gray-700 rounded-md p-3 text-white placeholder-gray-500 focus:ring-emerald-500 focus:border-emerald-500"
              />
              <Button 
                type="submit" 
                className="self-end bg-emerald-600 hover:bg-emerald-500 text-white"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Updating..." : "Update Policy"}
              </Button>
            </form>

            {lastAgentMessage && (
              <div className="mt-4 p-4 bg-emerald-900/30 border border-emerald-500/50 rounded-lg flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 mt-0.5 shrink-0" />
                <p className="text-emerald-100 text-sm">{lastAgentMessage}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Current Policy View */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="h-6 w-6 text-blue-400" />
              Current Rules
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-gray-400">Loading policy...</div>
            ) : policy ? (
              <div className="space-y-6">
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-gray-400">Max Automated Recovery Amount</h3>
                  <p className="text-lg text-white font-mono">₹{(policy.max_automated_amount / 100).toLocaleString()}</p>
                </div>
                
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-gray-400">Max Recovery Attempts</h3>
                  <p className="text-lg text-white font-mono">{policy.max_recovery_attempts} attempts</p>
                </div>

                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-gray-400">High Risk Requires Approval</h3>
                  <p className="text-lg text-white font-mono">{policy.high_risk_requires_approval ? "Yes" : "No"}</p>
                </div>

                {policy.high_risk_requires_approval && (
                  <div className="space-y-1">
                    <h3 className="text-sm font-medium text-gray-400">Approval Threshold</h3>
                    <p className="text-lg text-white font-mono">₹{(policy.approval_threshold / 100).toLocaleString()}</p>
                  </div>
                )}

                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-400">Allowed Actions</h3>
                  <div className="flex flex-wrap gap-2">
                    {policy.allowed_actions.split(',').map((action) => (
                      <span key={action} className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs font-medium">
                        {action}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-400">Failed to load policy.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
