import { useState } from "react";
import "./App.css";

const API_BASE = "";

function App() {
  const [request, setRequest] = useState(
    "I need a keyboard for programming"
  );
  const [budget, setBudget] = useState(3500);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState("");
  const [error, setError] = useState("");
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [transactionState, setTransactionState] = useState(null);
  const [view, setView] = useState("buyer");
  const [negotiationOffer, setNegotiationOffer] = useState("");
  const [negotiationLoading, setNegotiationLoading] = useState(false);
  const [negotiationResult, setNegotiationResult] = useState(null);
  const [merchantPolicy, setMerchantPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);
  const [policyStatus, setPolicyStatus] = useState("");
    async function loadMerchantInsights() {
    setInsightsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/merchant/insights`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to load merchant insights."
        );
      }

      setInsights(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setInsightsLoading(false);
    }
  }

    async function refreshAudit(transactionId) {
    if (!transactionId) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/audit/${transactionId}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to refresh audit trail."
        );
      }

      setTransactionState({
        status: data.status,
        retry_count: data.retry_count,
      });

      setResult((current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,
          audit: data.events,
          payment: current.payment
            ? {
                ...current.payment,
                order_id:
                  data.razorpay_order_id ||
                  current.payment.order_id,
              }
            : current.payment,
        };
      });
    } catch (err) {
      console.error("Audit refresh failed:", err);
    }
  }
    async function evaluatePurchase() {
    setLoading(true);
    setError("");
    setPaymentStatus("");
      setNegotiationResult(null);
      setNegotiationOffer("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/agent/purchase`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            request,
            max_budget: Number(budget),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail?.message ||
            data.detail ||
            "Agent purchase failed"
        );
      }

      setResult(data);
      await loadMerchantInsights();
      if (data.status === "blocked") {
        setPaymentStatus("AI purchase blocked by policy.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadRazorpayScript() {
    if (window.Razorpay) {
      return true;
    }

    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";

      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);

      document.body.appendChild(script);
    });
  }

  async function openCheckout(order, config, transactionId) {
  const scriptLoaded = await loadRazorpayScript();

  if (!scriptLoaded) {
    throw new Error("Unable to load Razorpay Checkout.");
  }
  let paymentFailed = false;
  const options = {
    key: config.key_id,
    amount: order.amount,
    currency: order.currency,
    name: "PruthviPayz",
    description: "AI Buyer Purchase",
    order_id: order.id,

    handler: async function (response) {
      try {
        setPaymentStatus("Payment received. Verifying...");

        const verifyResponse = await fetch(
          `${API_BASE}/api/payment/verify`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              order_id: response.razorpay_order_id,
              payment_id: response.razorpay_payment_id,
              signature: response.razorpay_signature,
            }),
          }
        );

        const verifyData = await verifyResponse.json();

        if (!verifyResponse.ok) {
          throw new Error(
            verifyData.detail?.message ||
              "Payment verification failed."
          );
        }

        setPaymentStatus(
          `Payment verified: ${verifyData.payment_id}`
        );
        await refreshAudit(transactionId);
      } catch (err) {
        setError(err.message);
        setPaymentStatus("");
      setNegotiationResult(null);
      setNegotiationOffer("");
      }
    },

    modal: {
  ondismiss: function () {
    if (!paymentFailed) {
      setPaymentStatus(
        `Checkout closed. Transaction: ${transactionId}`
      );
    }
  },
},

    theme: {
      color: "#63c7ef",
    },
  };
  
  const razorpay = new window.Razorpay(options);

  razorpay.on("payment.failed", async function (response) {
    paymentFailed = true;
    const orderId = response.error?.metadata?.order_id;
    const paymentId = response.error?.metadata?.payment_id;

    setPaymentStatus("Payment failed. Recording failure...");

    try {
      if (!orderId || !paymentId) {
        throw new Error(
          "Razorpay did not provide failure identifiers."
        );
      }

      const failureResponse = await fetch(
        `${API_BASE}/api/payment/failed`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            transaction_id: transactionId,
            razorpay_order_id: orderId,
            razorpay_payment_id: paymentId,
            reason:
              response.error?.description ||
              "Razorpay payment failed",
          }),
        }
      );

      const failureData = await failureResponse.json();

      if (!failureResponse.ok) {
        throw new Error(
          failureData.detail ||
            "Unable to record payment failure."
        );
      }

      setPaymentStatus(
        `Payment failed and recorded. Transaction: ${transactionId}`
      );
      await refreshAudit(transactionId);
    } catch (err) {
      setError(err.message);
      setPaymentStatus("");
      setNegotiationResult(null);
      setNegotiationOffer("");
    }
  });

  razorpay.open();
}

    async function approveNegotiationOpportunity() {
      if (policyLoading) {
        return;
      }

      setPolicyLoading(true);
      setPolicyStatus("");
      setError("");

      try {
        const response = await fetch(
          `${API_BASE}/api/merchant/policy`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              ai_negotiation_enabled: true,
              max_ai_discount: 299,
            }),
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              "Unable to update merchant negotiation policy."
          );
        }

        setMerchantPolicy(data.policy);
        setPolicyStatus(
          "AI negotiation approved. Maximum discount is now ₹299."
        );
      } catch (err) {
        setError(err.message);
      } finally {
        setPolicyLoading(false);
      }
    }

    async function negotiatePrice() {
      const transactionId = result?.transaction_id;
      const offer = Number(negotiationOffer);

      if (!transactionId || !offer || negotiationLoading) {
        return;
      }

      setNegotiationLoading(true);
      setNegotiationResult(null);
      setError("");

      try {
        const response = await fetch(
          `${API_BASE}/api/negotiation/propose`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              transaction_id: transactionId,
              buyer_offer: offer,
            }),
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail?.message ||
              data.detail ||
              "Negotiation request failed."
          );
        }

        setNegotiationResult(data);

        if (data.status === "approved") {
          const orderResponse = await fetch(
            `${API_BASE}/api/payment/create-negotiated-order`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                transaction_id: transactionId,
              }),
            }
          );

          const orderData = await orderResponse.json();

          if (!orderResponse.ok) {
            throw new Error(
              orderData.detail?.message ||
                orderData.detail ||
                "Unable to create negotiated Razorpay order."
            );
          }

          setResult((current) => ({
            ...current,
            payment: {
              provider: "razorpay",
              order_id: orderData.razorpay_order.id,
              amount: orderData.razorpay_order.amount,
              currency: orderData.razorpay_order.currency,
            },
            authorization: orderData.authorization,
          }));

          setPaymentStatus(
            `Negotiated price approved: ₹${data.final_price.toLocaleString("en-IN")}`
          );

          await refreshAudit(transactionId);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setNegotiationLoading(false);
      }
    }

    async function createPayment() {
    if (
      !result?.authorization?.authorized ||
      !result?.payment?.order_id ||
      (
        transactionState?.status === "PAYMENT_FAILED" &&
        transactionState?.retry_count >= 1
      )
    ) {
      return;
    }

    setPaymentLoading(true);
    setError("");
    setPaymentStatus("");
      setNegotiationResult(null);
      setNegotiationOffer("");

    try {
      const configResponse = await fetch(
        `${API_BASE}/api/payment/config`
      );

      const config = await configResponse.json();

      if (!configResponse.ok) {
        throw new Error(
          "Unable to load Razorpay configuration."
        );
      }

      await openCheckout(
        {
          id: result.payment.order_id,
          amount: result.payment.amount,
          currency: result.payment.currency,
        },
        config,
        result.transaction_id
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setPaymentLoading(false);
    }
  }

async function recoverPayment() {
  const transactionId = result?.authorization?.transaction_id;

  if (!transactionId) {
    return;
  }

  setPaymentLoading(true);
  setError("");
  setPaymentStatus("Checking recovery policy...");

  try {
    const recoveryResponse = await fetch(
      `${API_BASE}/api/recovery/retry`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transaction_id: transactionId,
        }),
      }
    );

    const recoveryData = await recoveryResponse.json();

    if (!recoveryResponse.ok) {
      throw new Error(
        recoveryData.detail ||
          "Recovery was not permitted."
      );
    }

    const configResponse = await fetch(
      `${API_BASE}/api/payment/config`
    );

    const config = await configResponse.json();

    if (!configResponse.ok) {
      throw new Error(
        "Unable to load Razorpay configuration."
      );
    }

    setPaymentStatus(
      `Recovery authorized. Retry #${recoveryData.retry_number}`
    );
    await refreshAudit(transactionId);
    await openCheckout(
      recoveryData.razorpay_order,
      config,
      transactionId
    );
  } catch (err) {
    setError(err.message);
    setPaymentStatus("");
      setNegotiationResult(null);
      setNegotiationOffer("");
  } finally {
    setPaymentLoading(false);
  }
}

  return (
    <main className="app">
      <section className="hero">
        <div className="badge">PRUTHVIPAYZ</div>

        <h1>Merchant Gateway for AI Buyers</h1>

        <p className="subtitle">
          An agentic commerce layer that lets AI buyers discover,
          evaluate, authorize, and purchase safely.
        </p>
        </section>
        <div className="mode-switch">
          <button
            className={view === "buyer" ? "mode-button active" : "mode-button"}
            onClick={() => setView("buyer")}
          >
            AI Buyer
          </button>
          <button
            className={view === "merchant" ? "mode-button active" : "mode-button"}
            onClick={() => { setView("merchant"); loadMerchantInsights(); }}
          >
            Merchant
          </button>
        </div>

        {view === "buyer" ? (
          <>


        <section className="panel">
        <div className="section-title">
          <span>01</span>
          Buyer Request
        </div>

        <label>What does the AI buyer want?</label>

        <textarea
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          rows={4}
        />

        <label>Maximum budget (₹)</label>

        <input
          type="number"
          value={budget}
          onChange={(e) => setBudget(e.target.value)}
          min="1"
        />

        <button onClick={evaluatePurchase} disabled={loading}>
          {loading ? "Evaluating..." : "Evaluate Purchase"}
        </button>

        {error && <div className="error">{error}</div>}
      </section>

            {result && (
        <section className="panel result-panel">
          <div className="section-title">
            <span>02</span>
            Live Agent Execution
          </div>

          <div className="trace-list">
            {result.audit?.map((event, index) => {
              const labels = {
                BUYER_REQUEST: "Buyer request received",
                CATALOG_SEARCH: "Merchant catalog searched",
                AI_PROVIDER_USED: "Gemini evaluated the request",
                PRODUCT_SELECTED: "Product selected",
                POLICY_CHECK: "Policy checks evaluated",
                AUTHORIZATION_GRANTED: "Purchase authorization granted",
                AUTHORIZATION_BLOCKED: "Purchase blocked by policy",
                ORDER_CREATED: "Razorpay order created",
                PAYMENT_SUCCESS: "Payment successful",
                PAYMENT_FAILED: "Payment failed",
                RECOVERY_TRIGGERED: "Recovery policy triggered",
                PAYMENT_RETRY: "Recovery retry authorized",
                RECOVERY_ORDER_CREATED: "Recovery order created",
              };

              return (
                <div
                  className="trace-row"
                  key={`${event.event_type}-${index}`}
                >
                  <div className="trace-marker">
                    {index + 1}
                  </div>

                  <div className="trace-content">
                    <strong>
                      {labels[event.event_type] || event.event_type}
                    </strong>
                    <small>{event.event_type}</small>
                  </div>

                  <span className="trace-status">DONE</span>
                </div>
              );
            })}
          </div>

          <div className="section-title">
            <span>03</span>
            Purchase Decision
          </div>

          <div className="decision-grid">
            <div>
              <small>PRODUCT</small>
              <strong>{result.product.selected_product_name}</strong>
            </div>

            <div>
              <small>PRICE</small>
              <strong>
                ₹{result.product.price.toLocaleString("en-IN")}
              </strong>
            </div>

            <div>
              <small>AI CONFIDENCE</small>
              <strong>
                {Math.round(result.product.confidence * 100)}%
              </strong>
            </div>

            <div>
              <small>PROVIDER</small>
              <strong>Gemini</strong>
            </div>
          </div>

          <div className="authority-card">
            <div>
              <small>BUYER AUTHORITY</small>
              <strong>
                ₹
                {result.authorization.buyer_max_amount.toLocaleString(
                  "en-IN"
                )}
              </strong>
            </div>

            <div>
              <small>APPROVED PURCHASE</small>
              <strong>
                ₹
                {result.authorization.approved_amount.toLocaleString(
                  "en-IN"
                )}
              </strong>
            </div>

            <div>
              <small>REMAINING AUTHORITY</small>
              <strong>
                ₹
                {(
                  result.authorization.buyer_max_amount -
                  result.authorization.approved_amount
                ).toLocaleString("en-IN")}
              </strong>
            </div>
          </div>

          <div className="reason">
            <small>WHY THE AGENT CHOSE IT</small>
            <p>{result.product.reason}</p>
          </div>


          {(result.status === "negotiation_required" || result.authorization.authorized) && !negotiationResult && (
            <div className="negotiation-card">
              <div className="section-title">
                <span>04</span>
                AI Negotiation
              </div>

              <p>
                Ask the merchant for a better price. The offer is checked
                against merchant policy and your spending authority.
              </p>

              <div className="negotiation-price-row">
                <div>
                  <small>CURRENT PRICE</small>
                  <strong>
                    ₹{result.product.price.toLocaleString("en-IN")}
                  </strong>
                </div>

                <div>
                  <small>BUYER AUTHORITY</small>
                  <strong>
                    ₹{result.authorization.buyer_max_amount.toLocaleString("en-IN")}
                  </strong>
                </div>

                <div>
                  <small>MAX AI DISCOUNT</small>
                  <strong>₹299</strong>
                </div>
              </div>

              <label>Your offer (₹)</label>
              <input
                type="number"
                value={negotiationOffer}
                onChange={(e) => setNegotiationOffer(e.target.value)}
                min="1"
                max={result.authorization.buyer_max_amount}
                placeholder="2200"
              />

              <button
                className="negotiation-button"
                onClick={negotiatePrice}
                disabled={negotiationLoading}
              >
                {negotiationLoading ? "Negotiating..." : "Make Offer"}
              </button>
            </div>
          )}

          {negotiationResult && (
            <div
              className={`negotiation-result ${
                negotiationResult.status === "approved"
                  ? "negotiation-approved"
                  : "negotiation-rejected"
              }`}
            >
              {negotiationResult.status === "approved" ? (
                <>
                  <div className="negotiation-result-label">
                    ✓ OFFER ACCEPTED
                  </div>

                  <h3>
                    ₹{negotiationResult.original_price.toLocaleString("en-IN")}
                    {" "}→{" "}
                    ₹{negotiationResult.final_price.toLocaleString("en-IN")}
                  </h3>

                  <p>
                    You saved ₹
                    {negotiationResult.discount.toLocaleString("en-IN")}
                  </p>

                  <div className="negotiation-checks">
                    <span>✓ Merchant policy passed</span>
                    <span>✓ Buyer authority passed</span>
                    <span>✓ New Razorpay order created</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="negotiation-result-label">
                    ✕ OFFER REJECTED
                  </div>

                  <h3>Merchant policy blocked the offer</h3>

                  <p>{negotiationResult.reason}</p>

                  <small>
                    Maximum AI discount: ₹
                    {negotiationResult.merchant_max_discount?.toLocaleString(
                      "en-IN"
                    ) ?? "299"}
                  </small>
                </>
              )}
            </div>
          )}

          <div className="checks">
            <div className="section-title">
              <span>04</span>
              Policy Guardrails
            </div>

            {Object.entries(
              result.audit.find(
                (event) => event.event_type === "POLICY_CHECK"
              )?.details?.checks || {}
            ).map(([check, passed]) => (
              <div className="check-row" key={check}>
                <span>{check.replaceAll("_", " ")}</span>

                <b className={passed ? "allowed" : "blocked"}>
                  {passed ? "PASS" : "BLOCK"}
                </b>
              </div>
            ))}
          </div>

          {result.authorization.authorized && result.payment && (
            <div className="payment-area">
              <div className="section-title">
                <span>05</span>
                Execute Payment
              </div>

              <div className="payment-summary">
                <small>AUTHORIZED RAZORPAY ORDER</small>
                <strong>
                  ₹
                  {result.authorization.approved_amount.toLocaleString(
                    "en-IN"
                  )}
                </strong>
                <span>
                  Order {result.payment.order_id}
                </span>
              </div>

              {transactionState?.status !== "PAYMENT_FAILED" ||
              transactionState?.retry_count < 1 ? (
                <button
                  className="pay-button"
                  onClick={createPayment}
                  disabled={paymentLoading}
                >
                  {paymentLoading
                    ? "Preparing Checkout..."
                    : `Pay ₹${result.authorization.approved_amount.toLocaleString(
                        "en-IN"
                      )} with Razorpay`}
                </button>
              ) : null}

              {paymentStatus && (
                <div className="payment-status">
                  {paymentStatus}
                </div>
              )}

              {transactionState?.status === "PAYMENT_FAILED" &&
                transactionState?.retry_count < 1 && (
                  <button
                    className="recovery-button"
                    onClick={recoverPayment}
                    disabled={paymentLoading}
                  >
                    {paymentLoading
                      ? "Checking Recovery..."
                      : "Recover Payment — Retry Once"}
                  </button>
                )}

              {transactionState?.status === "PAYMENT_FAILED" &&
                transactionState?.retry_count >= 1 && (
                  <div className="payment-status">
                    Recovery exhausted — further payment attempts are locked.
                    <br />
                    Retry limit: {transactionState.retry_count}/1
                  </div>
                )}
            </div>
          )}
        </section>
      )}

          {insights && (
        <section className="panel merchant-panel">
          <div className="section-title">
            <span>06</span>
            Merchant AI Insights
          </div>

          <div className="insight-grid">
            <div className="insight-card">
              <small>AI BUYER REQUESTS</small>
              <strong>{insights.total_ai_buyer_requests}</strong>
            </div>

            <div className="insight-card">
              <small>AVERAGE BUYER BUDGET</small>
              <strong>
                ₹{Number(insights.average_buyer_budget).toLocaleString(
                  "en-IN"
                )}
              </strong>
            </div>
          </div>

          {insights.top_products?.length > 0 && (
            <div className="insight-list">
              <div className="insight-heading">
                Top Requested Products
              </div>

              {insights.top_products.map((product) => (
                <div
                  className="insight-row"
                  key={product.product_id}
                >
                  <div>
                    <strong>{product.product_name}</strong>
                    <small>
                      ₹{product.price.toLocaleString("en-IN")}
                    </small>
                  </div>

                  <span>
                    {product.request_count} request
                    {product.request_count === 1 ? "" : "s"}
                  </span>
                </div>
              ))}
            </div>
          )}

          {insights.top_categories?.length > 0 && (
            <div className="insight-list">
              <div className="insight-heading">
                Top AI Buyer Categories
              </div>

              {insights.top_categories.map((category) => (
                <div
                  className="insight-row"
                  key={category.category}
                >
                  <strong>{category.category}</strong>
                  <span>
                    {category.request_count} request
                    {category.request_count === 1 ? "" : "s"}
                  </span>
                </div>
              ))}
            </div>
          )}
                    {insights.budget_gap_opportunities?.length > 0 && (
            <div className="opportunity-card">
              <div className="opportunity-label">
                AI BUYER OPPORTUNITY
              </div>

              <h3>
                {insights.budget_gap_opportunities[0].product_name}
              </h3>

              <p>
                AI buyers are requesting this product below its
                current catalog price.
              </p>

              <div className="opportunity-grid">
                <div>
                  <small>BUYER BUDGET</small>
                  <strong>
                    ₹
                    {insights.budget_gap_opportunities[0].buyer_budget.toLocaleString(
                      "en-IN"
                    )}
                  </strong>
                </div>

                <div>
                  <small>CURRENT PRICE</small>
                  <strong>
                    ₹
                    {insights.budget_gap_opportunities[0].current_price.toLocaleString(
                      "en-IN"
                    )}
                  </strong>
                </div>

                <div>
                  <small>PRICE GAP</small>
                  <strong>
                    ₹
                    {insights.budget_gap_opportunities[0].price_gap.toLocaleString(
                      "en-IN"
                    )}
                  </strong>
                </div>

                <div>
                  <small>REQUESTS</small>
                  <strong>
                    {insights.budget_gap_opportunities[0].request_count}
                  </strong>
                </div>
              </div>

              <div className="opportunity-action">
                Consider a lower-priced offer or promotion for this
                buyer segment.
              </div>
            </div>
          )}
        </section>
      )}

      </>
    ) : (
      <section className="merchant-console">

        <div className="merchant-header">
          <div>
            <div className="section-title">
              <span>01</span>
              Merchant Command Center
            </div>
            <h2>AI Commerce Control Plane</h2>
            <p>
              Control what AI buyers can discover, negotiate, and purchase.
            </p>
          </div>

          <div className="merchant-live">
            <span className="live-dot"></span>
            AI COMMERCE LIVE
          </div>
        </div>

        <div className="merchant-stats">
          <div className="merchant-stat">
            <small>AI BUYER REQUESTS</small>
            <strong>
              {insights?.total_ai_buyer_requests ?? "—"}
            </strong>
          </div>

          <div className="merchant-stat">
            <small>AVG BUYER BUDGET</small>
            <strong>
              {insights
                ? `₹${insights.average_buyer_budget.toLocaleString("en-IN")}`
                : "—"}
            </strong>
          </div>

          <div className="merchant-stat">
            <small>TOP CATEGORY</small>
            <strong>
              {insights?.top_categories?.[0]?.category ?? "—"}
            </strong>
          </div>

          <div className="merchant-stat">
            <small>AI OPPORTUNITIES</small>
            <strong>
              {insights?.budget_gap_opportunities?.length ?? 0}
            </strong>
          </div>
        </div>

        <div className="merchant-section">
          <div className="section-title">
            <span>02</span>
            Catalogue
          </div>

          <div className="catalogue-grid">
            {[
              {
                name: "Mechanical Keyboard",
                price: 2499,
                stock: 42,
                category: "Peripherals",
              },
              {
                name: "Wireless Mouse",
                price: 1299,
                stock: 68,
                category: "Peripherals",
              },
              {
                name: "USB-C Hub",
                price: 1799,
                stock: 35,
                category: "Accessories",
              },
              {
                name: "Laptop Stand",
                price: 1499,
                stock: 51,
                category: "Accessories",
              },
              {
                name: "Webcam",
                price: 2999,
                stock: 24,
                category: "Peripherals",
              },
            ].map((product) => (
              <div className="catalogue-card" key={product.name}>
                <div className="catalogue-product-top">
                  <span className="catalogue-category">
                    {product.category}
                  </span>
                  <span className="stock-badge">
                    {product.stock} in stock
                  </span>
                </div>

                <h3>{product.name}</h3>

                <strong>
                  ₹{product.price.toLocaleString("en-IN")}
                </strong>

                <div className="catalogue-controls">
                  <span>AI Discovery</span>
                  <b className="allowed">ON</b>

                  <span>AI Purchase</span>
                  <b className="allowed">ON</b>

                  <span>AI Negotiation</span>
                  <b className="allowed">READY</b>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="merchant-section">
          <div className="section-title">
            <span>03</span>
            AI Commerce Policy
          </div>

          <div className="policy-grid">
            <div className="policy-card">
              <small>AGENT PURCHASES</small>
              <strong>ENABLED</strong>
              <p>AI buyers may purchase approved products.</p>
            </div>

            <div className="policy-card">
              <small>AI NEGOTIATION</small>
              <strong>READY</strong>
              <p>Offer engine will respect merchant price limits.</p>
            </div>

            <div className="policy-card">
              <small>MAX RETRIES</small>
              <strong>1</strong>
              <p>Payment recovery is strictly bounded.</p>
            </div>

            <div className="policy-card">
              <small>HUMAN APPROVAL</small>
              <strong>ABOVE LIMIT</strong>
              <p>Actions outside policy require merchant review.</p>
            </div>
          </div>
        </div>

        <div className="merchant-section">
          <div className="section-title">
            <span>04</span>
            Revenue Opportunities
          </div>

          {insights?.budget_gap_opportunities?.length ? (
            <div className="merchant-opportunity">
              <div>
                <small>HIGH-INTENT DEMAND GAP</small>
                <h3>
                  {insights.budget_gap_opportunities[0].product_name}
                </h3>

                <p>
                  AI buyers are searching for this product below its current
                  price.
                </p>
              </div>

              <div className="opportunity-metrics">
                <div>
                  <small>BUYER BUDGET</small>
                  <strong>
                    ₹
                    {insights.budget_gap_opportunities[0].buyer_budget.toLocaleString(
                      "en-IN"
                    )}
                  </strong>
                </div>

                <div>
                  <small>PRICE GAP</small>
                  <strong>
                    ₹
                    {insights.budget_gap_opportunities[0].price_gap.toLocaleString(
                      "en-IN"
                    )}
                  </strong>
                </div>

                <div>
                  <small>REQUESTS</small>
                  <strong>
                    {insights.budget_gap_opportunities[0].request_count}
                  </strong>
                </div>
              </div>

              <div className="merchant-recommendation">
                <strong>AI RECOMMENDATION</strong>
                <p>
                  Enable bounded AI negotiation up to ₹
                  {insights.budget_gap_opportunities[0].price_gap.toLocaleString(
                    "en-IN"
                  )}{" "}
                  to recover this demand.
                </p>

                                <button
                  className="merchant-action"
                  onClick={approveNegotiationOpportunity}
                  disabled={policyLoading}
                >
                  {policyLoading
                    ? "Updating Policy..."
                    : "Approve AI Negotiation"}
                </button>

                {policyStatus && (
                  <div className="policy-status">
                    {policyStatus}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="merchant-empty">
              <div>
                <strong>No budget-gap opportunities detected yet.</strong>
                <p>
                  AI negotiation can still be enabled proactively for
                  high-intent buyers.
                </p>
              </div>

              <button
                className="merchant-action"
                onClick={approveNegotiationOpportunity}
                disabled={policyLoading}
              >
                {policyLoading
                  ? "Updating Policy..."
                  : "Approve AI Negotiation"}
              </button>

              {policyStatus && (
                <div className="policy-status">
                  {policyStatus}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="merchant-section">
          <div className="section-title">
            <span>05</span>
            Agent Trust Controls
          </div>

          <div className="trust-banner">
            <div>
              <strong>AI can recommend.</strong>
              <span>Policy decides.</span>
              <span>Razorpay executes.</span>
              <span>Audit proves.</span>
            </div>

            <div className="trust-status">
              7/7 POLICY CHECKS
            </div>
          </div>
        </div>

      </section>
    )}

    </main>
  );
}

export default App;