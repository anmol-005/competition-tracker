import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function AdminSettings() {
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold text-gray-100">Settings</h1>

      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">System Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-300">Dark Theme</span>
            <Button variant="secondary" size="sm" className="bg-blue-600 hover:bg-blue-700">
              Enabled
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-gray-300">Email Notifications</span>
            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-gray-200">
              Disabled
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">Security</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button variant="destructive" className="w-full">
            Reset Admin Password
          </Button>
          <Button variant="secondary" className="w-full">
            Manage API Keys
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
