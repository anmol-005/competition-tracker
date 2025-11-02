import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, Flag, Ban, ShieldCheck, UserPlus } from "lucide-react";

// ✅ define type for your user
interface User {
  id: number;
  name: string;
  role: "Admin" | "Analyst" | "Viewer";
  joined: string;
  status: "Active" | "Flagged" | "Banned";
}

export default function UserManagement() {
  const [searchQuery, setSearchQuery] = useState("");

  const users: User[] = [
    { id: 1, name: "jane_doe", role: "Admin", joined: "Jan 10, 2025", status: "Active" },
    { id: 2, name: "mark_analytics", role: "Analyst", joined: "Feb 14, 2025", status: "Flagged" },
    { id: 3, name: "alice_view", role: "Viewer", joined: "Mar 21, 2025", status: "Banned" },
  ];

  // ✅ add proper typing for handlers
  const handleFlag = (user: User) => {
    console.log(`Flagging user: ${user.name}`);
  };

  const handleBan = (user: User) => {
    console.log(`Banning user: ${user.name}`);
  };

  const handleUnban = (user: User) => {
    console.log(`Unbanning user: ${user.name}`);
  };

  const handlePromote = (user: User) => {
    console.log(`Promoting user: ${user.name}`);
  };

  const filteredUsers = users.filter((u) =>
    u.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold text-gray-100">User Management</h1>

      {/* Search & Filter */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 w-64 bg-[#1b1b1f] border-gray-700 text-gray-200"
            />
          </div>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white">
          <UserPlus className="h-4 w-4 mr-2" /> Add New User
        </Button>
      </div>

      {/* Users Table */}
      <Card className="bg-[#1b1b1f] border border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-200 font-semibold">
            Registered Users
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm text-gray-300">
              <thead>
                <tr className="bg-[#222226] border-b border-gray-700">
                  <th className="text-left px-4 py-3 font-medium text-gray-400">
                    Username
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-400">
                    Role
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-400">
                    Joined
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-400">
                    Status
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-gray-800 hover:bg-[#222226] transition"
                  >
                    <td className="px-4 py-3 font-medium text-gray-200">
                      {user.name}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant="secondary"
                        className={`${
                          user.role === "Admin"
                            ? "bg-blue-500/20 text-blue-400"
                            : user.role === "Analyst"
                            ? "bg-green-500/20 text-green-400"
                            : "bg-gray-500/20 text-gray-400"
                        }`}
                      >
                        {user.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-400">{user.joined}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-semibold px-2 py-1 rounded-full ${
                          user.status === "Active"
                            ? "bg-green-500/20 text-green-400"
                            : user.status === "Flagged"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-red-500/20 text-red-400"
                        }`}
                      >
                        {user.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-yellow-400 hover:text-yellow-300"
                        onClick={() => handleFlag(user)}
                      >
                        <Flag className="h-4 w-4 mr-1" /> Flag
                      </Button>
                      {user.status !== "Banned" ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-400 hover:text-red-300"
                          onClick={() => handleBan(user)}
                        >
                          <Ban className="h-4 w-4 mr-1" /> Ban
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-green-400 hover:text-green-300"
                          onClick={() => handleUnban(user)}
                        >
                          <ShieldCheck className="h-4 w-4 mr-1" /> Unban
                        </Button>
                      )}
                      {user.role !== "Admin" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-blue-400 hover:text-blue-300"
                          onClick={() => handlePromote(user)}
                        >
                          <ShieldCheck className="h-4 w-4 mr-1" /> Promote
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
