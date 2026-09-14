**Project Description:**&nbsp;  
We are building a fully **agentic order management system** using **LangChain agents and tool calling**. The system will support **order placement, order cancellation, and product enquiry**, with all actions tracked via proper database tables, audits and product specification PDFs ingested into a vector database for intelligent retrieval.

&nbsp;

**System Overview:**

The system will have a Master Orchestrator Agent that receives the user’s request, identifies the intent (order, cancel, enquiry), and routes it to the correct specialized agent:

1. **Order Agent** – Handles new order placement.  
   1. **Check Item Existence** – Verify if the requested product exists in inventory.  
   2. **Order Table Update** – Create or update an order record with fields:&nbsp;  
      1. orderID, productID, quantity, status, remarks, orderDate.  
   3. **Order Audit Table Update** – Log any changes with fields:  
      1. orderID, previousStatus, newStatus, timestamp, remarks.  
   4. **Inventory Update** – Deduct stock in the **Inventory Table** and record change in **Inventory Audit Table**.  
   5. **Customer Email Notification** – Send an order confirmation email to the customer.  
2. **Cancellation Agent** – Handles reversing an order (cancellation).  
   1. **Cancel Order** – Update the **Order Table** to reflect cancellation.  
   2. **Order Audit Update** – Log cancellation details in **Order Audit Table**.  
   3. **Restore Inventory** – Add back the stock to **Inventory Table** and record the action in **Inventory Audit Table**.  
   4. **Customer Email Notification** – Send a cancellation confirmation email.  
3. **Enquiry Agent** – Handles customer product information queries via VectorDB.  
   1. **Vector Database Setup** – Ingest product-related information for intelligent retrieval.  
      1. 5 product specification PDFs (3–4 pages each).  
      2. Each PDF includes details such as smart capabilities, Wi-Fi features, technical specifications, and service details.  
   2. **Query Handling:** When a customer asks about a product  
      1. Retrieve relevant details from VectorDB.  
      2. Summarize specifications and features  
      3. Provide direct responses to the customer.  
         &nbsp;

**Database Requirements:**

Four main tables will be created to support order and inventory tracking:

1. **Inventory Table:** productID, productName, quantityAvailable, price, lastUpdated.  
2. **Inventory Audit Table:** auditID, productID, changeType (add/remove/update), quantityChanged, timestamp, remarks.  
3. **Order Table:** orderID, productID, quantity, status, remarks, orderDate.  
4. **Order Audit Table:** auditID, orderID, previousStatus, newStatus, timestamp, remarks**.**

