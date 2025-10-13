import { Button } from "./ui/button"

export function TestShadcn() {
  return (
    <div className="p-8 space-y-4 bg-white rounded-lg shadow-md max-w-md mx-auto my-8">
      <h2 className="text-2xl font-bold text-gray-900">Shadcn/ui + Tailwind Test</h2>
      <p className="text-gray-600">If you see styled buttons below, the framework is working!</p>

      <div className="space-y-2">
        <Button variant="default" className="w-full">
          Default Button (Success Color)
        </Button>
        <Button variant="outline" className="w-full">
          Outline Button
        </Button>
        <Button variant="destructive" className="w-full">
          Destructive Button (Danger Color)
        </Button>
      </div>

      <p className="text-sm text-info font-semibold">
        ✅ Framework Integration Complete!
      </p>
    </div>
  );
}
