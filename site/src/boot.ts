// Browser entry point (kept apart from main.ts so tests can import the router without booting it).
import "./style.css";
import { loadBundle } from "./data/index";
import { boot } from "./main";

boot(loadBundle());
