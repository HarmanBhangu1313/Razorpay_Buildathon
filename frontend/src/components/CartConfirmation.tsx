'use client'
import React, { useState } from 'react';

export default function CartConfirmation({ cart, guardrails, onConfirm }: any) {
  const [loading, setLoading] = useState(false);
  
  const hasFailedGuardrails = guardrails && guardrails.some((g: any) => g.status === 'FAIL');
  const failureReason = guardrails?.find((g: any) => g.status === 'FAIL')?.reason;

  return (
    <div className={`border rounded-xl p-5 bg-white text-black shadow-lg mb-4 w-full ${hasFailedGuardrails ? 'border-red-300 ring-2 ring-red-100' : 'border-gray-200'}`}>
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
        <h3 className="font-bold text-lg text-gray-900">Order Summary</h3>
        {hasFailedGuardrails ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800">
            ❌ Guardrail Violation
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Guardrails Passed
          </span>
        )}
      </div>

      {hasFailedGuardrails && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-xs text-red-700">
          <p className="font-bold mb-1">🛑 Checkout Blocked</p>
          <p>{failureReason || "This order violates store or budget safety rules."}</p>
        </div>
      )}

      <div className="space-y-3 mb-4">
        {cart.items && cart.items.map((item: any) => (
          <div key={item.product_id} className="flex justify-between items-center text-sm">
            <div className="flex flex-col">
              <span className="font-semibold text-gray-900">{item.name}</span>
              <span className="text-xs text-gray-500">Qty: {item.quantity}</span>
            </div>
            <span className="font-bold text-gray-900">₹{(item.price * item.quantity).toLocaleString('en-IN')}</span>
          </div>
        ))}
      </div>

      <div className="border-t border-gray-200 pt-3 mb-5">
        <div className="flex justify-between items-baseline">
          <span className="text-base font-medium text-gray-700">Total Amount</span>
          <span className="text-2xl font-extrabold text-black">₹{cart.final_total ? cart.final_total.toLocaleString('en-IN') : cart.total?.toLocaleString('en-IN')}</span>
        </div>
        {cart.user_budget && (
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Stated Budget:</span>
            <span className="font-medium text-gray-700">₹{cart.user_budget.toLocaleString('en-IN')}</span>
          </div>
        )}
        <p className="text-xs text-gray-400 mt-1">Includes all applicable taxes & free shipping</p>
      </div>

      <button 
        onClick={async () => {
          setLoading(true);
          await onConfirm();
          setLoading(false);
        }}
        disabled={loading || hasFailedGuardrails}
        className={`w-full rounded-lg py-3.5 px-4 font-bold text-base shadow-md transition duration-150 ease-in-out flex items-center justify-center gap-2 ${
          hasFailedGuardrails 
            ? 'bg-red-600 text-white cursor-not-allowed opacity-80' 
            : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white'
        }`}
      >
        {loading ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating Payment Link...
          </>
        ) : hasFailedGuardrails ? (
          <>
            <span>Payment Blocked by Guardrail</span>
          </>
        ) : (
          <>
            <span>Proceed to Payment</span>
            <span>→</span>
          </>
        )}
      </button>
      
      <p className="text-center text-xs text-gray-400 mt-2">
        🔒 Verified by AgentShop Deterministic Guardrails
      </p>
    </div>
  );
}
