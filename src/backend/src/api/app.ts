import cors from "cors";
import express from "express";
import helmet from "helmet";

export const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());

app.get("/api/health", (_request, response) => {
  response.json({ status: "ok" });
});

// Feature routers will be mounted under /api as each use case is implemented.
